/**********************************************************************
 Copyright (c) 2020-2023, Unitree Robotics.Co.Ltd. All rights reserved.
***********************************************************************/
/**********************************************************************
Версия v0.1(250313)
Описание: Определите состояние, в котором робот свободно стоит на полу, сохраняя при этом заданную позу и высоту
Функции
- calcOP: Расчет положения стопы у цели, расчет положения стопы у цели на основе текущей позы (крен, тангаж, рыскание) и высоты
- Допустимый максимальный/минимальный крен, тангаж, рыскание, определение высоты
***********************************************************************/
#ifndef FREESTAND_H
#define FREESTAND_H

#include "FSM/FSMState.h"

class State_FreeStand : public FSMState{
public:
    State_FreeStand(CtrlComponents *ctrlComp);
    ~State_FreeStand(){}
    void enter();
    void run();
    void exit();
    FSMStateName checkChange();
private:
    Vec3 _initVecOX;
    Vec34 _initVecXP;
    float _rowMax, _rowMin;
    float _pitchMax, _pitchMin;
    float _yawMax, _yawMin;
    float _heightMax, _heightMin;

    Vec34 _calcOP(float row, float pitch, float yaw, float height);
    void _calcCmd(Vec34 vecOP);
};

#endif  // FREESTAND_H