import os
import json
import yaml
import warnings
from yaml import SafeLoader
from typing import Dict, Any
from collections import defaultdict, ChainMap

Payload = Dict[str, Any]


def parse_config(config: Payload) -> Payload:
    env = os.environ.get("ENV", "development")
    main_config = config.get("app", None)

    if main_config is None:
        raise KeyError("app configs not found.")

    if env not in config.keys():
        warnings.warn(f"No specific configuration found for {env}")

    env_config = config.get(env, {})

    config = defaultdict(dict)
    for key in list(set(list(main_config.keys()) + list(env_config.keys()))):
        mcfg = main_config.get(key, None)
        ecfg = env_config.get(key, None)

        if mcfg is None and ecfg is None:
            continue

        elif not mcfg or not ecfg:
            config[key] = list(filter(None, [mcfg, ecfg]))[0]

        elif type(mcfg) != type(ecfg):
            raise TypeError(
                f"{key} from cannettes and env configs must be of same type"
            )

        elif type(mcfg) == type(ecfg) == dict:
            # -- env cfg must override in case of duplicates
            config[key] = {**mcfg, **ecfg}

        else:
            # -- last case, type is not dict, override with env config
            config[key] = ecfg

    return config


def parse_client_config(filename: str, *configs: Payload) -> None:
    """generate config json file"""
    client_cfg = dict(ChainMap(*configs))
    with open(filename, "w") as writer:
        writer.write(f"var config = {json.dumps(client_cfg)};")


def map_env(config: Payload) -> Payload:
    for k, v in config.items():
        if isinstance(v, str) and v.startswith("${"):
            v = os.environ.get(v.split("{")[1].strip("}"), None)
            if v is None:
                raise KeyError(f"ENV variable {k} does not exist")
            config[k] = v
        elif isinstance(v, dict):
            config[k] = map_env(v)
    return config


def get_config(path: str) -> Payload:
    with open(path, "r") as f:
        config = yaml.load(f, SafeLoader)
        config = parse_config(config)
        config = map_env(config)
    return config
