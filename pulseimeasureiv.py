#!/usr/bin python
import visa
import csv
import numpy as np

def exportFile(filename, data):
  with open(filename, 'wt') as csvfile:
    csvfile.write(data)
    
def openCommPort(IP):
  #Open communication ports
  rm = visa.ResourceManages('@py')
  instr = rm.open_resource('TCPIP::' + IP + '::INSTR')

def initSMU(smu, src, rng, lim):
  """
  initSMU(smu, src, rng, lim)
  smu: "smua" or smub"
  src: 0 - volts, 1 - amps
  rng: source range
  lim: measure limit
  """
  instr.write(smu + ".reset()")
  instr.write(smu + ".source.func = " + smu + "." + sourceFunctions[src]) #SMU A will act as a current source and voltmeter
  instr.write(smu + ".nvbuffer1.appendmode = 1")  #New readings are appended to the existing data
  instr.write(smu + ".measure.nplc = " + str(nplc) + "")
  instr.write(smu + ".measure.autozero = smua.AUTOZERO_ONCE")
  
def setLimit(smu, src, lim):
  if sourceFunctions[src] == 'OUTPUT_DCVOLTS':
    func = 'i'
  elif sourceFunctions[src] == 'OUTPUT_DCAMPS':
    func = 'v'
  instr.write(smu + ".source.limit" + func + " = " + str(lim))

def setRange(smu, src, rng):
  if sourceFunctions[src] == 'OUTPUT_DCVOLTS':
    func = 'v'
  elif sourceFunctions[src] == 'OUTPUT_DCAMPS':
    func = 'i'
  instr.write(smu + ".source.range" + func + " = " + str(rng))
  
def configPulse(smu, curr, wdt):
  instr.write(smu + ".trigger.source.action = " + smu + ".ENABLE")
  instr.write(smu + ".trigger.measure.action = " + smu + ".ENABLE")
  instr.write(smu + ".trigger.measure.v(" + smu + ".nvbuffer1)")

  instr.write("trigger.timer[1].count = 1")
  instr.write("trigger.timer[1].passthrough = false")
  instr.write("trigger.timer[1].stimulus = " + smu + ".trigger.ARMED_EVENT_ID")
  instr.write(smu + ".trigger.source.stimulus = 0")
  instr.write(smu + ".trigger.measure.stimulus = trigger.timer[1].EVENT_ID")
  instr.write(smu + ".trigger.endpulse.stimulus = trigger.timer[1].EVENT_ID")
  instr.write(smu + ".trigger.endpulse.action = " + smu + ".SOURCE_IDLE")
  instr.write(smu + ".trigger.count = 1")
  instr.write(smu + ".trigger.arm.count = 1")

  instr.write(smu + ".source.trigger.listi({" + str(curr) + "e-6})")
  instr.write("trigger.timer[1].delay = " + str(wdt) + "")

###########
  
sourceFunctions = {
  0: 'OUTPUT_DCVOLTS',
  1: 'OUTPUT_DCAMPS',
}
limitv = 0.9 #Maximum voltage limit (in volts)
limiti = 0.001 #Maximum current limit (in amperes)
v = '' #Will hold the voltage readings
i = '' #Will hold the current readings
pulses = 100 #Number of pulses per train
loops = 10 #Number of pulse trains
width = 0.02 #Pulse width (in seconds)
milliamps = 0.308  #Current level of the pulses (in milliamps)
nplc = 0.005  #Number of power cycles for integration

openCommPort('169.254.0.1')

###########

#Initialise SMUs
initSMU('smua', 1, 0.001, limitv)
initSMU('smub', 0, 0.001, limiti) #Check the range here

#Configure pulse
configPulse('smua',milliamps,width)

#Turn both sources on
instr.write("smua.source.output = smua.OUTPUT_ON")
instr.write("smub.source.output = smub.OUTPUT_ON")

for l in range(0, loops):
  #Clear data buffers each loop
  instr.write("smua.nvbuffer1.clear()")
  instr.write("smub.nvbuffer1.clear()")
  instr.write("waitcomplete()") #Wait for the buffers to be cleared. Not sure if necessary
  
  #For loop creating the pulse train at a fixed current. Horribly long.
  instr.write("for a = 1,100 do smua.trigger.initiate() smub.measure.i(smub.nvbuffer1) waitcomplete() end"))
  instr.write("waitcomplete()") #Again, not sure if necessary 
  
  v = v + instr.query("x = printbuffer(1,smua.nvbuffer1.n,smua.nvbuffer1.readings)")
  i = i + instr.query("x = printbuffer(1,smub.nvbuffer1.n,smub.nvbuffer1.readings)")
  exportfile(filename + "-" + str(milliamps) + "-" + str(l) + ".txt", v + i)
  
#Turn both sources off
instr.write("smua.source.output = smua.OUTPUT_OFF")
instr.write("smub.source.output = smub.OUTPUT_OFF")
instr.close()
