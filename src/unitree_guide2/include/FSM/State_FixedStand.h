/**********************************************************************
 Copyright (c) 2020-2023, Unitree Robotics.Co.Ltd. All rights reserved.
***********************************************************************/
/**********************************************************************
Отпустите v0.1(250313)
Описание: Определяет состояние, при котором робот стоит в фиксированном положении, при котором робот не двигается и сохраняет постоянное положение

Отпустите v0.2(250313)
- Введите каждое положение сустава, в котором находится targetPos B1
***********************************************************************/
#ifndef FIXEDSTAND_H
#define FIXEDSTAND_H

#include "FSM/FSMState.h"

class State_FixedStand : public FSMState{
public:
    State_FixedStand(CtrlComponents *ctrlComp);
    ~State_FixedStand(){}
    void enter();
    void run();
    void exit();
    FSMStateName checkChange();

private:
    // float _targetPos[12] = {0.0, 0.67, -1.3, 0.0, 0.67, -1.3, 
    //                         0.0, 0.67, -1.3, 0.0, 0.67, -1.3};
    float _targetPos[12] = {0.0, 0.5, -1.3, 
                            -0.0, 0.5, -1.3, 
                            0.0, 0.5, -1.3, 
                            -0.0, 0.5, -1.3};                            
    float _startPos[12];
    float _duration = 1000;   //steps
    float _percent = 0;       //%
};

#endif  // FIXEDSTAND_H