# Aviation Risk Estimation Module

## Introduction

In this module, we are trying to simulate aviation accident through NATS and quantify the evolving risk during the accident. More specifically, there are two major contribitions in this module. First of all, we convert the aviation accident recordings from NTSB into data that can be identified through NATS.  Secondly, we build up a risk estimation pipline using deep learning and tree-based method according to the NTSB data. Once the module is able to accurately capture enough details in the aviation accident, more scientific research about aviation accident can be done according to the module then. 

## Requirement

The risk estimation module is built using deep learning and tree-based method. In detail, the following package are needed for this module

- Pytorch 1.4.0
- catboost 0.23
- xgboost 1.0.2

## Major Files and Module Explanation 

- `aviationr.py` is the major module which follows the template format for NATS simulation
  - `class AviationRisk` is the major class 
    - function `accident_simulator` provides the interface between NTSB and NATS 
- `aviationr_model.py` is providing necessary classes for pre-trained model and the class for risk estimation 
  - `class RNNModel` provides the architecture of hieachical LSTM
  - `class SequentialPrediction` provides the architecture of hieachical markovian
  - `class HierarchicalSoftmax` provides the architecture of hieachical softmax
  - `class RiskEstimator` provides the pipline for estimating the risk for each event in aviation accident

## Methodology

### Accident Simulator

Accident simulator is for exploring what and how we build NSTB accident recordings into NATS simulator. According to our current understanding about NATS. The following interface will cooperate to simulate the aviaion accident

- [x] aircraftInterface
- [ ] environmentInterface
- [ ] controllerInterface
- [ ] pilotInterface

Currently, we only implement a simple simulator through setting the phase of flight. We find the relationship of definition between NATS and NTSB manually. And the table needs to be improved furthermore with more knowledge. Following is an example of current table. 

|      | NTSB_CODE | NTSB                                                         | NATS_CODE | NATS                                  |
| ---- | --------- | ------------------------------------------------------------ | --------- | ------------------------------------- |
| 0    | 500       | Standing                                                     | 1.0       | FLIGHT_PHASE_ORIGIN_GATE              |
| 1    | 501       | Standing - pre-flight                                        | 1.0       | FLIGHT_PHASE_ORIGIN_GATE              |
| 2    | 502       | Standing - starting engine(s)                                | 1.0       | FLIGHT_PHASE_ORIGIN_GATE              |
| 3    | 503       | Standing - engine(s) operating                               | 1.0       | FLIGHT_PHASE_ORIGIN_GATE              |
| 4    | 504       | Standing - engine(s) not operating                           | 1.0       | FLIGHT_PHASE_ORIGIN_GATE              |
| 5    | 505       | Standing - idling rotors                                     | 1.0       | FLIGHT_PHASE_ORIGIN_GATE              |
| 6    | 510       | Taxi                                                         |           |                                       |
| 7    | 511       | Taxi - pushback/tow                                          | 2.0       | FLIGHT_PHASE_PUSHBACK                 |
| 8    | 512       | Taxi - to takeoff                                            | 4.0       | FLIGHT_PHASE_TAXI_DEPARTING           |
| 9    | 513       | Taxi - from landing                                          | 22.0      | FLIGHT_PHASE_TAXI_ARRIVING            |
| 10   | 514       | Taxi - aerial                                                |           |                                       |
| 11   | 520       | Takeoff                                                      | 6.0       | FLIGHT_PHASE_TAKEOFF                  |
| 12   | 521       | Takeoff - roll/run                                           | 6.0       | FLIGHT_PHASE_TAKEOFF                  |
| 13   | 522       | Takeoff - initial climb                                      | 6.0       | FLIGHT_PHASE_TAKEOFF                  |
| 14   | 523       | Takeoff - aborted                                            | 6.0       | FLIGHT_PHASE_TAKEOFF                  |
| 15   | 530       | Climb                                                        | 7.0       | FLIGHT_PHASE_CLIMBOUT                 |
| 16   | 531       | Climb - to cruise                                            | 9.0       | FLIGHT_PHASE_CLIMB_TO_CRUISE_ALTITUDE |
| 17   | 540       | Cruise                                                       | 11.0      | FLIGHT_PHASE_CRUISE                   |
| 18   | 541       | Cruise - normal                                              | 11.0      | FLIGHT_PHASE_CRUISE                   |
| 19   | 542       | Maneuvering - holding (IFR)                                  | 12.0      | FLIGHT_PHASE_HOLD_IN_ENROUTE_PATTERN  |
| 20   | 550       | Descent                                                      | 13.0      | FLIGHT_PHASE_TOP_OF_DESCENT           |
| 21   | 551       | Descent - normal                                             | 13.0      | FLIGHT_PHASE_TOP_OF_DESCENT           |
| 22   | 552       | Descent - emergency                                          | 13.0      | FLIGHT_PHASE_TOP_OF_DESCENT           |
| 23   | 553       | Descent - uncontrolled                                       | 13.0      | FLIGHT_PHASE_TOP_OF_DESCENT           |
| 24   | 560       | Approach                                                     | 16.0      | FLIGHT_PHASE_APPROACH                 |
| 25   | 561       | Approach - VFR pattern - downwind                            | 16.0      | FLIGHT_PHASE_APPROACH                 |
| 26   | 562       | Approach - VFR pattern - turn to base                        | 16.0      | FLIGHT_PHASE_APPROACH                 |
| 27   | 563       | Approach - VFR pattern - base leg/base to final              | 16.0      | FLIGHT_PHASE_APPROACH                 |
| 28   | 564       | Approach - VFR pattern - final approach                      | 17.0      | FLIGHT_PHASE_FINAL_APPROACH           |
| 29   | 565       | Go-around (VFR)                                              | 18.0      | FLIGHT_PHASE_GO_AROUND                |
| 30   | 566       | Approach - Initial approach fix (IAF) to final approach fix (FAF)/outer marker (IFR) | 17.0      | FLIGHT_PHASE_FINAL_APPROACH           |
| 31   | 567       | Approach - final approach fix (FAF)/outer marker to threshold (IFR) | 17.0      | FLIGHT_PHASE_FINAL_APPROACH           |
| 32   | 568       | Approach - circling (IFR)                                    | 17.0      | FLIGHT_PHASE_FINAL_APPROACH           |
| 33   | 569       | Missed approach (IFR)                                        |           |                                       |
| 34   | 570       | Landing                                                      | 20.0      | FLIGHT_PHASE_LAND                     |
| 35   | 571       | Landing - flare/touchdown                                    | 20.0      | FLIGHT_PHASE_LAND                     |
| 36   | 572       | Landing - roll                                               | 20.0      | FLIGHT_PHASE_LAND                     |
| 37   | 573       | Landing - aborted                                            | 20.0      | FLIGHT_PHASE_LAND                     |
| 38   | 574       | Emergency landing                                            | 20.0      | FLIGHT_PHASE_LAND                     |
| 39   | 575       | Emergency landing after takeoff                              | 20.0      | FLIGHT_PHASE_LAND                     |
| 40   | 576       | Emergency descent/landing                                    | 20.0      | FLIGHT_PHASE_LAND                     |
| 41   | 580       | Maneuvering                                                  |           |                                       |
| 42   | 581       | Maneuvering - aerial application                             |           |                                       |
| 43   | 582       | Maneuvering - turn to reverse direction                      |           |                                       |
| 44   | 583       | Maneuvering - turn to landing area (emergency)               |           |                                       |
| 45   | 590       | Hover                                                        |           |                                       |
| 46   | 591       | Hover - in ground effect                                     |           |                                       |
| 47   | 592       | Hover - out of ground effect                                 |           |                                       |
| 48   | 600       | Other                                                        |           |                                       |
| 49   | 610       | Unknown                                                      |           |                                       |

### Risk Estimator

We further implement a risk estimation module based on deep learning and tree-based method. We build a hierchical LSTM as a sequential model to simulate the sequential events in an aviation accident. Each sequential events will be represented using one hot encoding and be classified into minor/ substantial/ destroyed which is also defined according to NTSB. The risk estimator modules contains the following two major modules 

#### Future Event Predictoin and Hierarhical Tree-based Embedding: 

We propose a tree-based embedding method to map the original hierarhical event representation into a low-dimensional vectors. These embedding will be used in an LSTM to predict the future events. The models are saved in sample_data/aviationR.  and the code are saved in simulation_method/aviationr_model.py. Here, `Pytorch` is required since deep learning modules implemented in the proposed framework. 

#### Risk Event Quantification

Predict the future risk and give its uncertainty. To achieve this, Both Xgboost and Catboost will be used combining with the future event prediction module. 

