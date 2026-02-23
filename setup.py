from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'sem_map_vision'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='sensor',
    maintainer_email='sensor@todo.todo',
    description='TODO: Package description',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'no_pc_vision_node = sem_map_vision.no_pc_vision:main',
            'mapper_node = sem_map_vision.mapper_node:main',
            'goal_checker_node = sem_map_vision.goal_checker_node:main',
        ],
    },
)
