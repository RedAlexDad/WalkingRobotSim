FROM osrf/ros:humble-desktop

# Объявляем ARG сразу после FROM — это обязательно для BuildKit
ARG ROBOT_TYPE=Go2

# Установка базовых утилит
RUN apt-get update && apt-get install -y \
    python3-colcon-common-extensions \
    python3-rosdep \
    git \
    wget \
    nano \
    && rm -rf /var/lib/apt/lists/*

# Установка пакетов Navigation2, SLAM Toolbox, интеграции Gazebo, управления роботом и LiDAR
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    # Управление роботом: ros2-control и ros2-controllers
    # Фреймворк управления роботами в ROS 2
    ros-humble-ros2-control \                     
    # Набор контроллеров для ros2-control (например, joint_trajectory_controller)
    ros-humble-ros2-controllers \       
    ros-humble-controller-manager \     
    ros-humble-controller-interface \     
    ros-humble-joint-state-broadcaster \
    ros-humble-hardware-interface \
    ros-humble-angles \

    # Navigation2: навигация и локализация
    # Основной пакет для навигации роботов
    ros-humble-navigation2 \                      
    # Инструменты для запуска системы навигации
    ros-humble-nav2-bringup \                     
    # Сервер карт для навигации
    ros-humble-nav2-map-server \                  
    # Алгоритм адаптивного Монте-Карло локализации (AMCL)
    ros-humble-nav2-amcl \                        
    # Планировщик путей
    ros-humble-nav2-planner \                     
    # Контроллер движения (например, DWB)
    ros-humble-nav2-controller \                  

    # SLAM Toolbox: построение карт и локализация
    # Пакет для выполнения SLAM (синхронная или асинхронная работа)
    ros-humble-slam-toolbox \
    ros-humble-cartographer \
    ros-humble-cartographer-* \                     

    # Интеграция Gazebo
    # Интеграция Gazebo с ros2-control
    ros-humble-gazebo-ros2-control \              
    # Дополнительные плагины для Gazebo
    ros-humble-gazebo-plugins \                   
    # Базовая интеграция ROS 2 с Gazebo
    ros-humble-gazebo-ros \           
    ros-humble-gazebo-ros-pkgs \

    # Локализация и калибровка
    # Пакет для объединения данных от IMU, LiDAR и других датчиков
    ros-humble-robot-localization \               
    # Инструменты для работы с IMU (инерциальными датчиками)
    ros-humble-imu-tools \                        
    ros-humble-imu-sensor-broadcaster \

    # Xacro: работа с URDF-моделями
    # Инструмент для работы с макросами в URDF
    ros-humble-xacro \                            

    # LiDAR Velodyne: драйверы и обработка данных
    # Мета-пакет для работы с устройствами Velodyne
    ros-humble-velodyne \                         
    # Драйвер для получения данных с устройства Velodyne
    ros-humble-velodyne-driver \                  
    # Преобразование сырых данных в точечное облако
    ros-humble-velodyne-pointcloud \              
    # Преобразование данных в формат LaserScan
    ros-humble-velodyne-laserscan \     
    # Для работы с плагинами     
    ros-humble-velodyne-gazebo-plugins \     

    # Дополнительные инструменты
    # Интеграция Point Cloud Library (PCL) с ROS 2
    ros-humble-pcl-ros \                          
    # Визуализация данных в RViz2
    ros-humble-rviz2 \                            
    # Инструменты для работы с TF2 (трансформации)
    ros-humble-tf2-tools \                        
    # Публикация состояния шарниров (joints)
    ros-humble-joint-state-publisher \    
    ros-humble-joint-state-publisher-gui \        
    # Управление роботом с клавиатуры
    ros-humble-teleop-twist-keyboard \            
    # Поддержка геймпадов и джойстиков
    ros-humble-joy \                              

    # Утилиты для работы с сетью и топиками
    # Утилиты для работы с топиками ROS 2
    ros-humble-topic-tools \                      
    # Инструменты для диагностики состояния робота
    ros-humble-diagnostic-updater \               

    # Очистка кэша
    && rm -rf /var/lib/apt/lists/*

# Установка Unitree SDK
RUN git clone https://github.com/unitreerobotics/unitree_sdk2.git /tmp/unitree_sdk2 && \
    cd /tmp/unitree_sdk2 && \
    mkdir build && cd build && \
    cmake .. -DCMAKE_INSTALL_PREFIX=/opt/unitree_robotics && \
    make -j$(nproc) && \
    make install && \
    rm -rf /tmp/unitree_sdk2

# Указание CMAKE_PREFIX_PATH, чтобы CMake мог найти SDK
ARG CMAKE_PREFIX_PATH=""
ENV CMAKE_PREFIX_PATH="/opt/unitree_robotics:${CMAKE_PREFIX_PATH}"

RUN apt-get update && apt-get install -y \
    lsb-release wget gnupg && \
    wget https://packages.osrfoundation.org/gazebo.key -O - | apt-key add - && \
    sh -c 'echo "deb http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" > /etc/apt/sources.list.d/gazebo-stable.list' && \
    apt-get update && \
    apt-get install -y ignition-fortress

# Установка PyTorch C++ API (LibTorch)
RUN wget https://download.pytorch.org/libtorch/cpu/libtorch-shared-with-deps-2.2.2%2Bcpu.zip && \
    unzip libtorch-shared-with-deps-2.2.2+cpu.zip -d /opt && \
    rm libtorch-shared-with-deps-2.2.2+cpu.zip

# Добавляем путь к Torch в CMake
ENV CMAKE_PREFIX_PATH="/opt/libtorch:/opt/unitree_robotics:$CMAKE_PREFIX_PATH"

# Установка LCM (Lightweight Communications and Marshalling)
RUN apt-get update && apt-get install -y \
    liblcm-dev \
    liblcm1 \
    liblcm-bin \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория для проекта
WORKDIR /root/ros2_ws
COPY . .

# Дополнительная защита — если кто-то переопределит ARG, проверим корректность
RUN if [ -z "$ROBOT_TYPE" ]; then \
        echo "ERROR: ROBOT_TYPE not set!"; exit 1; \
    fi && \
    case $ROBOT_TYPE in \
        Go1|Go2) echo "Building for robot: $ROBOT_TYPE" ;; \
        *) echo "ERROR: ROBOT_TYPE must be Go1 or Go2, got: $ROBOT_TYPE"; exit 1;; \
    esac && \
    . /opt/ros/humble/setup.sh && \
    rm -rf build install log && \
    colcon build --symlink-install \
        --cmake-args \
          -DCMAKE_BUILD_TYPE=Release \
          -DROBOT_TYPE:STRING=${ROBOT_TYPE}

# Установка переменных окружения
ARG LD_LIBRARY_PATH=""
ENV LD_LIBRARY_PATH="/usr/local/lib:/opt/ros/humble/lib:/opt/libtorch/lib:$LD_LIBRARY_PATH"
ARG AMENT_PREFIX_PATH=""
ENV AMENT_PREFIX_PATH="/opt/ros/humble:$AMENT_PREFIX_PATH"

# Подготовка окружения
RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc && \
    echo "source /root/ros2_ws/install/setup.bash" >> ~/.bashrc && \
    echo "export LD_LIBRARY_PATH=/usr/local/lib:/opt/ros/humble/lib:/opt/libtorch/lib:\$LD_LIBRARY_PATH" >> ~/.bashrc

# Копируем скрипт приветствия в контейнер
COPY startup.bash /root/startup.bash

# Добавляем запуск при входе в контейнер
RUN chmod +x /root/startup.bash && \
    echo "bash /root/startup.bash" >> /root/.bashrc

CMD ["bash"]
