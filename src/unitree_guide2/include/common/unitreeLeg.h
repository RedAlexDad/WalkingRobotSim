/**********************************************************************
 Copyright (c) 2020-2023, Unitree Robotics.Co.Ltd. All rights reserved.
***********************************************************************/
/**********************************************************************
Версия 0.1(250313)
Описание: Определение класса для реализации ног робота Unitree, кинематика и управление движением ног.
Функции
- Класс четвероногих: получает идентификатор ноги, длину каждого звена и вектор положения от бедра к туловищу в качестве параметров
- calcPEe2H, calcPEe2B: Вычисляет положение концевого эффектора относительно координат бедра или тела, используя заданный угол наклона сустава.
- calcVEe: Вычисление скорости концевого привода
- calcQ, calcQd: Вычисление угла соединения или угловой скорости при заданном положении или скорости вращения
- calcTau: Вычисление крутящего момента с использованием угла соединения и силы
- caclJaco: Расчет якобиевых матриц конечных эффекторов для углов соединения
- q1_ik, q2_ik, q3_ik: расчет обратной кинематики, соответственно
- Класс Go1Leg: реализуйте ногу модели робота, наследующую класс QuadrupedLeg, сохраните длину ноги и начальные настройки конкретной модели робота в качестве конструктора

Версия 0.2(250313)
- Класс B1 также определен на основе описания робота unitree_ros_master
- Go1 const.результаты проверки xacro подтверждают, что каждое значение определено как thigh_offset / thigh_length / calf_length кинетического значения
- B1 также является постоянным.Определяется как кинетическое значение в xacro
***********************************************************************/
#ifndef UNITREELEG_H
#define UNITREELEG_H

#include "common/mathTypes.h"
#include "common/enumClass.h"

class QuadrupedLeg
{
public:
    QuadrupedLeg(int legID, float abadLinkLength, float hipLinkLength,
                 float kneeLinkLength, Vec3 pHip2B);
    ~QuadrupedLeg() {}
    Vec3 calcPEe2H(Vec3 q);
    Vec3 calcPEe2B(Vec3 q);
    Vec3 calcVEe(Vec3 q, Vec3 qd);
    Vec3 calcQ(Vec3 pEe, FrameType frame);
    Vec3 calcQd(Vec3 q, Vec3 vEe);
    Vec3 calcQd(Vec3 pEe, Vec3 vEe, FrameType frame);
    Vec3 calcTau(Vec3 q, Vec3 force);
    Mat3 calcJaco(Vec3 q);
    Vec3 getHip2B() { return _pHip2B; }

protected:
    float q1_ik(float py, float pz, float b2y);
    float q3_ik(float b3z, float b4z, float b);
    float q2_ik(float q1, float q3, float px,
                float py, float pz, float b3z, float b4z);
    float _sideSign;
    const float _abadLinkLength, _hipLinkLength, _kneeLinkLength;
    const Vec3 _pHip2B;
};


class Go1Leg : public QuadrupedLeg
{
public:
    Go1Leg(const int legID, const Vec3 pHip2B) : QuadrupedLeg(legID, 0.08, 0.213, 0.213, pHip2B) {}
    ~Go1Leg() {}
};

class Go2Leg : public QuadrupedLeg
{
public:
    Go2Leg(const int legID, const Vec3 pHip2B) : QuadrupedLeg(legID, 0.0955, 0.213, 0.213, pHip2B) {}
    ~Go2Leg() {}
};


#endif // UNITREELEG_H