// -*- mode:c++ -*-

#include <drobots.ice>

module drobots {
  interface RobotFactory {
    RobotController* make(Robot* bot, int id);
    DetectorController* makeDetector(int id);
  };

  interface Strategy {
    void position(Point pointTransmitter, int idTransmitter);
    void detectorEnemies(int idDetector, Point pointTransmitter, int enemies);
  };

  interface RobotControllerAttacker extends Attacker, Strategy, RobotController{
    void robotsDetected(Point pointTransmitter, int idTransmitter, int enemies);
  };

  interface RobotControllerDefender extends Defender, Strategy, RobotController {};

  interface RobotControllerComplete extends Attacker, Defender, Strategy, RobotController {};
};
