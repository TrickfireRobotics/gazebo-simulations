#include "chrono/collision/bullet/ChCollisionSystemBullet.h"
#include "chrono/core/ChDataPath.h"
#include "chrono/geometry/ChTriangleMeshConnected.h"
#include "chrono/physics/ChLinkMotorRotationAngle.h"
#include "chrono/physics/ChSystemSMC.h"

#include "chrono_vehicle/ChVehicleDataPath.h"
#include "chrono_vehicle/terrain/SCMTerrain.h"
#include "chrono_vehicle/visualization/ChScmVisualizationVSG.h"
#include "chrono_vsg/ChVisualSystemVSG.h"

using namespace chrono;

// -----------------------------------------------------------------------------
// Tunable parameters
// -----------------------------------------------------------------------------

enum class TireType { CYLINDRICAL, LUGGED };
TireType tire_type = TireType::LUGGED;

double mesh_resolution = 0.04;

bool enable_bulldozing = true;
bool enable_active_domains = true;

// When true, soil properties vary by position via MySoilParams callback.
// When false, uniform soil properties are used instead.
bool var_params = true;

// -----------------------------------------------------------------------------
// Location-dependent soil properties callback.
// Note: location is in the SCM reference frame; vehicle moves in -Y direction.
// -----------------------------------------------------------------------------

class MySoilParams : public vehicle::SCMTerrain::SoilParametersCallback {
  public:
    virtual void Set(const ChVector3d& loc, double& Bekker_Kphi, double& Bekker_Kc,
                     double& Bekker_n, double& Mohr_cohesion, double& Mohr_friction,
                     double& Janosi_shear, double& elastic_K, double& damping_R) override {
        if (loc.y() > 0) {
            // Soft soil
            Bekker_Kphi = 0.2e6;
            Bekker_Kc = 0;
            Bekker_n = 1.1;
            Mohr_cohesion = 0;
            Mohr_friction = 30;
            Janosi_shear = 0.01;
            elastic_K = 4e7;
            damping_R = 3e4;
        } else {
            // LETE sand
            Bekker_Kphi = 5301e3;
            Bekker_Kc = 102e3;
            Bekker_n = 0.793;
            Mohr_cohesion = 1.3e3;
            Mohr_friction = 31.1;
            Janosi_shear = 1.2e-2;
            elastic_K = 4e8;
            damping_R = 3e4;
        }
    }
};

// -----------------------------------------------------------------------------

int main(int argc, char* argv[]) {
    SetChronoDataPath(CHRONO_DATA_PATH);
    vehicle::SetVehicleDataPath(CHRONO_VEHICLE_DATA_PATH);

    vehicle::ChWorldFrame::SetYUP();

    double tire_rad = 0.8;
    ChVector3d tire_center(0, 0.02 + tire_rad, -1.5);

    // System
    ChSystemSMC sys;
    sys.SetGravityY();
    sys.SetNumThreads(4, 8, 1);
    sys.SetCollisionSystem(chrono_types::make_shared<ChCollisionSystemBullet>());

    auto mtruss = chrono_types::make_shared<ChBody>();
    mtruss->SetFixed(true);
    sys.Add(mtruss);

    // Wheel body
    auto wheel = chrono_types::make_shared<ChBody>();
    sys.Add(wheel);
    wheel->SetMass(500);
    wheel->SetInertiaXX(ChVector3d(20, 20, 20));
    wheel->SetPos(tire_center + ChVector3d(0, 0.3, 0));

    auto material = chrono_types::make_shared<ChContactMaterialSMC>();
    switch (tire_type) {
        case TireType::LUGGED: {
            auto trimesh = ChTriangleMeshConnected::CreateFromWavefrontFile(
                GetChronoDataFile("models/tractor_wheel/tractor_wheel.obj"));

            auto vis_shape = chrono_types::make_shared<ChVisualShapeTriangleMesh>();
            vis_shape->SetMesh(trimesh);
            vis_shape->SetColor(ChColor(0.3f, 0.3f, 0.3f));
            wheel->AddVisualShape(vis_shape);

            auto ct_shape = chrono_types::make_shared<ChCollisionShapeTriangleMesh>(
                material, trimesh, false, false, 0.01);
            wheel->AddCollisionShape(ct_shape, ChFrame<>(VNULL, ChMatrix33<>(1)));
            break;
        }
        case TireType::CYLINDRICAL: {
            double radius = 0.5;
            double width = 0.4;
            auto ct_shape =
                chrono_types::make_shared<ChCollisionShapeCylinder>(material, radius, width);
            wheel->AddCollisionShape(ct_shape, ChFrame<>(ChVector3d(0), QuatFromAngleY(CH_PI_2)));

            auto vis_shape = chrono_types::make_shared<ChVisualShapeCylinder>(radius, width);
            vis_shape->SetColor(ChColor(0.3f, 0.3f, 0.3f));
            wheel->AddVisualShape(vis_shape, ChFrame<>(VNULL, QuatFromAngleY(CH_PI_2)));
            break;
        }
    }
    wheel->EnableCollision(true);

    auto motor = chrono_types::make_shared<ChLinkMotorRotationAngle>();
    motor->SetSpindleConstraint(ChLinkMotorRotation::SpindleConstraint::OLDHAM);
    motor->SetAngleFunction(chrono_types::make_shared<ChFunctionRamp>(0, CH_PI / 4.0));
    motor->Initialize(wheel, mtruss, ChFrame<>(tire_center, QuatFromAngleY(CH_PI_2)));
    sys.Add(motor);

    // Terrain
    vehicle::SCMTerrain terrain(&sys);

    // SCMTerrain uses ISO frame (Z up); rotate to match Y-up world frame
    terrain.SetReferenceFrame(ChCoordsys<>(ChVector3d(0, 0, 0), QuatFromAngleX(-CH_PI_2)));

    double length = 6;
    double width = 2;
    terrain.Initialize(width, length, mesh_resolution);

    if (var_params) {
        auto my_params = chrono_types::make_shared<MySoilParams>();
        terrain.RegisterSoilParametersCallback(my_params);
    } else {
        terrain.SetSoilParameters(0.2e6,  // Bekker Kphi
                                  0,      // Bekker Kc
                                  1.1,    // Bekker n exponent
                                  0,      // Mohr cohesion (Pa)
                                  30,     // Mohr friction (degrees)
                                  0.01,   // Janosi shear coefficient (m)
                                  4e7,    // Elastic stiffness (Pa/m)
                                  3e4);   // Damping (Pa·s/m)
    }

    if (enable_bulldozing) {
        terrain.EnableBulldozing(true);
        terrain.SetBulldozingParameters(55, 1, 5, 6);
    }

    if (enable_active_domains) {
        terrain.AddActiveDomain(wheel, ChVector3d(0, 0, 0),
                                ChVector3d(0.5, 2 * tire_rad, 2 * tire_rad));
    }

    terrain.SetPlotType(vehicle::SCMTerrain::PLOT_PRESSURE_YIELD, 0, 30000.2);
    terrain.SetColormap(ChColormap::Type::COPPER);
    terrain.SetMeshWireframe(true);

    // Visualization
    auto visSCM = chrono_types::make_shared<vehicle::ChScmVisualizationVSG>(&terrain);
    auto vis = chrono_types::make_shared<vsg3d::ChVisualSystemVSG>();
    vis->AttachSystem(&sys);
    vis->AttachPlugin(visSCM);
    vis->SetWindowTitle("SCM deformable terrain");
    vis->AddCamera(ChVector3d(3.0, 2.0, 0.0), ChVector3d(0, tire_rad, 0));
    vis->SetWindowSize(1280, 800);
    vis->SetWindowPosition(100, 100);
    vis->SetCameraVertical(CameraVerticalDir::Y);
    vis->SetCameraAngleDeg(40.0);
    vis->SetLightIntensity(1.0f);
    vis->SetLightDirection(1.5 * CH_PI_2, CH_PI_4);
    vis->Initialize();

    // Simulation loop
    while (vis->Run()) {
        vis->BeginScene();
        vis->SetCameraTarget(wheel->GetPos());
        vis->Render();
        vis->EndScene();

        sys.DoStepDynamics(0.002);
    }

    return 0;
}
