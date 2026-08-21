import esphome.codegen as cg
from esphome.core import entity_helpers
import esphome.config_validation as cv
from esphome.components import myhomeiot_ble_host, esp32_ble_tracker
from esphome import const, automation
from esphome.const import (
    CONF_ID,
    CONF_INTERVAL,
    CONF_MAC_ADDRESS,
)

CODEOWNERS = ["@dvb666"]
AUTO_LOAD = ["sensor", "select", "myhomeiot_ble_client2"]
DEPENDENCIES = ["myhomeiot_ble_host"]

CONF_BLE_HOST = "ble_host"
CONF_ERROR_COUNTING = "error_counting"
CONF_RAW_SOIL = "raw_soil"

mclh_09_gateway_ns = cg.esphome_ns.namespace("mclh_09_gateway")
Mclh09Gateway = mclh_09_gateway_ns.class_(
    "Mclh09Gateway", cg.Component
)
# Actions
Mclh09GatewayForceUpdateAction = mclh_09_gateway_ns.class_("Mclh09GatewayForceUpdateAction", automation.Action)

CONFIG_SCHEMA = (
    cv.Schema(
        {
            cv.GenerateID(): cv.declare_id(Mclh09Gateway),
            cv.GenerateID(CONF_BLE_HOST): cv.use_id(myhomeiot_ble_host.MyHomeIOT_BLEHost),
            cv.Required(CONF_MAC_ADDRESS): cv.ensure_list(cv.mac_address),
            cv.Optional(CONF_INTERVAL, default="60min"): cv.positive_time_period_milliseconds,
            cv.Optional(CONF_ERROR_COUNTING, default=False): cv.boolean,
            cv.Optional(CONF_RAW_SOIL, default=False): cv.boolean,
        }
    )
    .extend(cv.COMPONENT_SCHEMA)
)
FORCE_UPDATE_ACTION_SCHEMA = cv.Schema(
    {
        cv.GenerateID(CONF_ID): cv.use_id(Mclh09Gateway),
    }
)

def versiontuple(v):
    return tuple(map(int, (v.split("."))))

async def to_code(config):
    addr_list = []
    for it in config[CONF_MAC_ADDRESS]:
      addr_list.append(it.as_hex)
    var = cg.new_Pvariable(config[CONF_ID], addr_list, config[CONF_INTERVAL], config[CONF_ERROR_COUNTING], config[CONF_RAW_SOIL])
    ble_host = await cg.get_variable(config[CONF_BLE_HOST])
    cg.add(var.set_ble_host(ble_host))

    batt_fields = (entity_helpers.register_device_class("battery") << 0) | (entity_helpers.register_unit_of_measurement("%") << 8) | (0 << 16) | (0 << 24) | (0 << 25) | (0 << 26)
    temp_fields = (entity_helpers.register_device_class("temperature") << 0) | (entity_helpers.register_unit_of_measurement("°C") << 8) | (0 << 16) | (0 << 24) | (0 << 25) | (0 << 26)
    lumi_fields = (entity_helpers.register_device_class("illuminance") << 0) | (entity_helpers.register_unit_of_measurement("lx") << 8) | (0 << 16) | (0 << 24) | (0 << 25) | (0 << 26)
    soil_fields = (0 << 0) | (0 << 8) | (0 << 16) | (0 << 24) | (0 << 25) | (0 << 26)
    if not config[CONF_RAW_SOIL]:
        soil_fields = (entity_helpers.register_device_class("moisture") << 0) | (entity_helpers.register_unit_of_measurement("%") << 8) | (0 << 16) | (0 << 24) | (0 << 25) | (0 << 26)
    humi_fields = (entity_helpers.register_device_class("humidity") << 0) | (entity_helpers.register_unit_of_measurement("%") << 8) | (0 << 16) | (0 << 24) | (0 << 25) | (0 << 26)
    rssi_fields = (entity_helpers.register_device_class("signal_strength") << 0) | (entity_helpers.register_unit_of_measurement("dBm") << 8) | (entity_helpers.register_icon("mdi:signal") << 16) | (0 << 24) | (0 << 25) | (2 << 26)
    error_fields = (0 << 0) | (0 << 8) | (entity_helpers.register_icon("mdi:alert-circle") << 16) | (0 << 24) | (0 << 25) | (2 << 26)
    alert_fields = (0 << 0) | (0 << 8) | (entity_helpers.register_icon("mdi:alarm-light") << 16) | (0 << 24) | (0 << 25) | (0 << 26)
    cg.add(var.set_sensor_fields(batt_fields, temp_fields, lumi_fields, soil_fields, humi_fields, rssi_fields, error_fields, alert_fields))

    from esphome.core import CORE
    num_sensors = len(config[CONF_MAC_ADDRESS]) * 7
    CORE.platform_counts.setdefault("sensor", 0)
    CORE.platform_counts["sensor"] += num_sensors

    num_selects = len(config[CONF_MAC_ADDRESS]) * 1
    CORE.platform_counts.setdefault("select", 0)
    CORE.platform_counts["select"] += num_selects

    await cg.register_component(var, config)


@automation.register_action(
    "mclh_09_gateway.force_update", Mclh09GatewayForceUpdateAction, FORCE_UPDATE_ACTION_SCHEMA, synchronous=True
)
async def ble_write_to_code(config, action_id, template_arg, args):
    parent = await cg.get_variable(config[CONF_ID])
    var = cg.new_Pvariable(action_id, template_arg, parent)
    return var
