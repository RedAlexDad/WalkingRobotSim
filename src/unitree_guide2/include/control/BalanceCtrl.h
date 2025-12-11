/**********************************************************************
 Copyright (c) 2020-2023, Unitree Robotics.Co.Ltd. All rights reserved.
***********************************************************************/

/**********************************************************************
Версия 0.1(250313)
Описание: Классы, которые реализуют алгоритмы управления балансом, вычисляют усилие для поддержания равновесия и перемещения, а также решают задачи оптимизации
 на основе QP для получения оптимальной силы контакта с ногой
Функции
- Класс BalanceCtrl: Подготовьте расчет силы, необходимой для поддержания равновесия, на основе информации о массе и инерции робота
- Конструктор BalanceCtrl: Общая масса, матрица инерции (3x3), матрица преобразования силы в 6x6-Матрица преобразования крутящего момента, вес для управления балансом
- calF: Рассчитайте усилие для поддержания равновесия, используя матрицы Якоби
- calMatirxA: установите матрицу соотношения силы и крутящего момента (A-матрицу) на основе положения ног робота и текущего состояния вращения
- calVectorBd: Рассчитайте целевой вектор для уравновешивания усилия, используя скорость изменения ускорения и угловой скорости
- calConstraints: установка ограничений QP в зависимости от количества соприкасающихся ног
- solveQP: расчет оптимального усилия ног с использованием QP
***********************************************************************/

#ifndef BALANCECTRL_H
#define BALANCECTRL_H

#include "common/mathTypes.h"
#include "thirdParty/quadProgpp/QuadProg++.hh"
#include "common/unitreeRobot.h"

#ifdef COMPILE_DEBUG
#include "common/PyPlot.h"
#endif // COMPILE_DEBUG

class BalanceCtrl
{
public:
    BalanceCtrl(double mass, Mat3 Ib, Mat6 S, double alpha, double beta);
    BalanceCtrl(QuadrupedRobot *robModel);
    Vec34 calF(Vec3 ddPcd, Vec3 dWbd, RotMat rotM, Vec34 feetPos2B, VecInt4 contact);
#ifdef COMPILE_DEBUG
    void setPyPlot(PyPlot *plot) { _testPlot = plot; }
#endif // COMPILE_DEBUG
private:
    void calMatrixA(Vec34 feetPos2B, RotMat rotM, VecInt4 contact);
    void calVectorBd(Vec3 ddPcd, Vec3 dWbd, RotMat rotM);
    void calConstraints(VecInt4 contact);
    void solveQP();

    Mat12 _G, _W, _U;
    Mat6 _S;
    Mat3 _Ib;
    Vec6 _bd;
    Vec3 _g;
    Vec3 _pcb;
    Vec12 _F, _Fprev, _g0T;
    double _mass, _alpha, _beta, _fricRatio;
    Eigen::MatrixXd _CE, _CI;
    Eigen::VectorXd _ce0, _ci0;
    Eigen::Matrix<double, 6, 12> _A;
    Eigen::Matrix<double, 5, 3> _fricMat;

    quadprogpp::Matrix<double> G, CE, CI;
    quadprogpp::Vector<double> g0, ce0, ci0, x;

#ifdef COMPILE_DEBUG
    PyPlot *_testPlot;
#endif // COMPILE_DEBUG
};

#endif // BALANCECTRL_H