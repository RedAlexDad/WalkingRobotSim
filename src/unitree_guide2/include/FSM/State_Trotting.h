/**********************************************************************
 Copyright (c) 2020-2023, Unitree Robotics.Co.Ltd. All rights reserved.
***********************************************************************/

/**********************************************************************
Версия v0.1(250313)
Описание: Класс, который определяет состояние рыси в FSM, выполняя перекрестные движения на четырех ногах с сохранением равновесия.
Функции
- State_Trotting: Создан с использованием модели ходьбы рысью (с внутренними частями Go1)
- calcBalanceKp: Настройка коэффициента баланса - > Не определено
- calcQQd: Расчет целевого положения стопы и скорости
- calcTau: Рассчитайте крутящий момент, приложенный к каждой ноге
- calcCmd: Примените к роботу окончательную команду ходьбы
- setHighCmd: Установите скорость передвижения робота, используя данные, введенные пользователем
- Класс AvgCov: класс, который вычисляет среднее значение и ковариацию, а также среднюю величину погрешностей положения робота и угла наклона
***********************************************************************/

#ifndef TROTTING_H
#define TROTTING_H

#include "FSM/FSMState.h"
#include "Gait/GaitGenerator.h"
#include "control/BalanceCtrl.h"

class State_Trotting : public FSMState
{
public:
    State_Trotting(CtrlComponents *ctrlComp);
    ~State_Trotting();
    void enter();
    void run();
    void exit();
    virtual FSMStateName checkChange();
    void setHighCmd(double vx, double vy, double wz);

private:
    void calcTau();
    void calcQQd();
    void calcCmd();
    virtual void getUserCmd();
    void calcBalanceKp();
    bool checkStepOrNot();

    GaitGenerator *_gait;
    Estimator *_est;
    QuadrupedRobot *_robModel;
    BalanceCtrl *_balCtrl;

    // Rob State
    Vec3 _posBody, _velBody;
    double _yaw, _dYaw;
    Vec34 _posFeetGlobal, _velFeetGlobal;
    Vec34 _posFeet2BGlobal;
    RotMat _RobRotMat, _G2BRotMat;
    Vec12 _q;

    // Robot command
    Vec3 _pcd;
    Vec3 _vCmdGlobal, _vCmdBody;
    double _yawCmd, _dYawCmd;
    double _dYawCmdPast;
    Vec3 _wCmdGlobal;
    Vec34 _posFeetGlobalGoal, _velFeetGlobalGoal;
    Vec34 _posFeet2BGoal, _velFeet2BGoal;
    RotMat _Rd;
    Vec3 _ddPcd, _dWbd;
    Vec34 _forceFeetGlobal, _forceFeetBody;
    Vec34 _qGoal, _qdGoal;
    Vec12 _tau;

    // Control Parameters
    double _gaitHeight;
    Vec3 _posError, _velError;
    Mat3 _Kpp, _Kdp, _Kdw;
    double _kpw;
    Mat3 _KpSwing, _KdSwing;
    Vec2 _vxLim, _vyLim, _wyawLim;
    Vec4 *_phase;
    VecInt4 *_contact;

    // Calculate average value
    AvgCov *_avg_posError = new AvgCov(3, "_posError", true, 1000, 1000, 1);
    AvgCov *_avg_angError = new AvgCov(3, "_angError", true, 1000, 1000, 1000);
};

#endif // TROTTING_H