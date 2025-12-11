/**********************************************************************
 Copyright (c) 2020-2023, Unitree Robotics.Co.Ltd. All rights reserved.
***********************************************************************/

/**********************************************************************
Версия 0.1(250313)
Описание: Файл hair на C++, в котором используется библиотека Eigen для определения векторов и матриц, необходимых для математических операций и структур данных.
Функции
- Vec2 ~ 6: Представляет реальный вектор с 2,3,4,6 измерениями (используется для выражения положения, скорости, ускорения и т.д.)
- Quat: кватернионный вектор в четырех измерениях
- VecInt4: Четырехмерный целочисленный вектор
- Vec12, Vec18: реальный вектор в 12D, 18D
- VecX: вектор с динамическим размером
- RotMat: матрица вращения 3x3, представляющая вращение объекта в трехмерном пространстве
- HomoMat: однородная матрица преобразования 4x4, представляющая трехмерное преобразование
- Mat2, Mat3, Mat6: преобразование в матрицы 2x2, 3x3, 6x6
- I3, I12, I18: преобразование единичных матриц размером 3x3, 12x12, 18x18
- vec12ToVec34: Преобразование 12-мерной матрицы размером 3x4
- vec34ToVec12: Преобразование матрицы 3x4 обратно в 12D
***********************************************************************/
#ifndef MATHTYPES_H
#define MATHTYPES_H

#include <eigen3/Eigen/Dense>

/************************/
/******** Vector ********/
/************************/
// 2x1 Vector
using Vec2 = typename Eigen::Matrix<double, 2, 1>;

// 3x1 Vector
using Vec3 = typename Eigen::Matrix<double, 3, 1>;

// 4x1 Vector
using Vec4 = typename Eigen::Matrix<double, 4, 1>;

// 6x1 Vector
using Vec6 = typename Eigen::Matrix<double, 6, 1>;

// Quaternion
using Quat = typename Eigen::Matrix<double, 4, 1>;

// 4x1 Integer Vector
using VecInt4 = typename Eigen::Matrix<int, 4, 1>;

// 12x1 Vector
using Vec12 = typename Eigen::Matrix<double, 12, 1>;

// 18x1 Vector
using Vec18 = typename Eigen::Matrix<double, 18, 1>;

// Dynamic Length Vector
using VecX = typename Eigen::Matrix<double, Eigen::Dynamic, 1>;

/************************/
/******** Matrix ********/
/************************/
// Rotation Matrix
using RotMat = typename Eigen::Matrix<double, 3, 3>;

// Homogenous Matrix
using HomoMat = typename Eigen::Matrix<double, 4, 4>;

// 2x2 Matrix
using Mat2 = typename Eigen::Matrix<double, 2, 2>;

// 3x3 Matrix
using Mat3 = typename Eigen::Matrix<double, 3, 3>;

// 3x3 Identity Matrix
#define I3 Eigen::MatrixXd::Identity(3, 3)

// 3x4 Matrix, each column is a 3x1 vector
using Vec34 = typename Eigen::Matrix<double, 3, 4>;

// 6x6 Matrix
using Mat6 = typename Eigen::Matrix<double, 6, 6>;

// 12x12 Matrix
using Mat12 = typename Eigen::Matrix<double, 12, 12>;

// 12x12 Identity Matrix
#define I12 Eigen::MatrixXd::Identity(12, 12)

// 18x18 Identity Matrix
#define I18 Eigen::MatrixXd::Identity(18, 18)

// Dynamic Size Matrix
using MatX = typename Eigen::Matrix<double, Eigen::Dynamic, Eigen::Dynamic>;

/************************/
/****** Functions *******/
/************************/
inline Vec34 vec12ToVec34(Vec12 vec12)
{
    Vec34 vec34;
    for (int i(0); i < 4; ++i)
    {
        vec34.col(i) = vec12.segment(3 * i, 3);
    }
    return vec34;
}

inline Vec12 vec34ToVec12(Vec34 vec34)
{
    Vec12 vec12;
    for (int i(0); i < 4; ++i)
    {
        vec12.segment(3 * i, 3) = vec34.col(i);
    }
    return vec12;
}

#endif // MATHTYPES_H