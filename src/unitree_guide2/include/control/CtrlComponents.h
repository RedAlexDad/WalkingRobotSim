/**********************************************************************
 Copyright (c) 2020-2023, Unitree Robotics.Co.Ltd. All rights reserved.
***********************************************************************/
/**********************************************************************
Версия 0.1(250313)Добавить комментарий Дополнительные действия
Описание: Управление компонентами управления роботом, данные датчиков, модель робота, схема ходьбы, контроль равновесия, оценка состояния и т.д.
Функции
- LowlevelCmd: сохранить команду низкого уровня
- LowlevelState: низкоуровневое хранение данных датчиков
- контакт: соприкасается ли каждая нога с полом
- фаза: Фаза походки каждой ноги
- *контакт, * фаза: Начальное состояние парения в воздухе, начальная фаза походки
- sendRecv(): Получение команд низкого уровня и данных с датчиков через IOinterface
- runWaveGen (): Расчет цикла ходьбы и состояния контакта ног, создание схемы ходьбы.
- setAllStacne, setAllSwing, setStarWave: Определите, в каком состоянии робот будет держать свои ноги (полностью на земле / полностью в воздухе / при ходьбе).
- geneObj: оценка состояния робота на основе данных датчиков, создание контроллера для поддержания баланса
***********************************************************************/
#ifndef CTRLCOMPONENTS_H
#define CTRLCOMPONENTS_H

#include "message/LowlevelCmd.h"
#include "message/LowlevelState.h"
#include "interface/IOInterface.h"
#include "interface/CmdPanel.h"
#include "common/unitreeRobot.h"
#include "Gait/WaveGenerator.h"
#include "control/Estimator.h"
#include "control/BalanceCtrl.h"
#include <string>
#include <iostream>

#ifdef COMPILE_DEBUG
#include "common/PyPlot.h"
#endif  // COMPILE_DEBUG

struct CtrlComponents{
public:
    CtrlComponents(IOInterface *ioInter):ioInter(ioInter){
        lowCmd = new LowlevelCmd();
        lowState = new LowlevelState();
        contact = new VecInt4;
        phase = new Vec4;
        *contact = VecInt4(0, 0, 0, 0);
        *phase = Vec4(0.5, 0.5, 0.5, 0.5);
    }
    ~CtrlComponents(){
        delete lowCmd;
        delete lowState;
        delete ioInter;
        delete robotModel;
        delete waveGen;
        delete estimator;
        delete balCtrl;
#ifdef COMPILE_DEBUG
        delete plot;
#endif  // COMPILE_DEBUG
    }
    LowlevelCmd *lowCmd;
    LowlevelState *lowState;
    IOInterface *ioInter;
    QuadrupedRobot *robotModel;
    WaveGenerator *waveGen;
    Estimator *estimator;
    BalanceCtrl *balCtrl;

#ifdef COMPILE_DEBUG
    PyPlot *plot;
#endif  // COMPILE_DEBUG

    VecInt4 *contact;
    Vec4 *phase;

    double dt;
    bool *running;
    CtrlPlatform ctrlPlatform;

    void sendRecv(){
        ioInter->sendRecv(lowCmd, lowState);
    }

    void runWaveGen(){
        waveGen->calcContactPhase(*phase, *contact, _waveStatus);
    }

    void setAllStance(){
        _waveStatus = WaveStatus::STANCE_ALL;
    }

    void setAllSwing(){
        _waveStatus = WaveStatus::SWING_ALL;
    }

    void setStartWave(){
        _waveStatus = WaveStatus::WAVE_ALL;
    }

    void geneObj(){
        estimator = new Estimator(robotModel, lowState, contact, phase, dt);
        balCtrl = new BalanceCtrl(robotModel);

#ifdef COMPILE_DEBUG
        plot = new PyPlot();
        balCtrl->setPyPlot(plot);
        estimator->setPyPlot(plot);
#endif  // COMPILE_DEBUG
    }

private:
    WaveStatus _waveStatus = WaveStatus::SWING_ALL;

};

#endif  // CTRLCOMPONENTS_H