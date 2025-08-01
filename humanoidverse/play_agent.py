import os
import sys
from pathlib import Path

import hydra
from hydra.utils import instantiate
from hydra.core.hydra_config import HydraConfig
from hydra.core.config_store import ConfigStore
from omegaconf import OmegaConf
from humanoidverse.utils.logging import HydraLoggerBridge
import logging
from utils.config_utils import *  # noqa: E402, F403

# add argparse arguments

from humanoidverse.utils.config_utils import *  # noqa: E402, F403
from loguru import logger

import threading
from pynput import keyboard

@hydra.main(config_path="config", config_name="base_play")
def main(override_config: OmegaConf):
    # logging to hydra log file
    hydra_log_path = os.path.join(HydraConfig.get().runtime.output_dir, "eval.log")
    logger.remove()
    logger.add(hydra_log_path, level="DEBUG")

    # Get log level from LOGURU_LEVEL environment variable or use INFO as default
    console_log_level = os.environ.get("LOGURU_LEVEL", "INFO").upper()
    logger.add(sys.stdout, level=console_log_level, colorize=True)

    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger().addHandler(HydraLoggerBridge())

    os.chdir(hydra.utils.get_original_cwd())

    if override_config.play is not None:
        has_config = True
        play = Path(override_config.play)
        config_path = play.parent / "config.yaml"
        if not config_path.exists():
            config_path = play.parent.parent / "config.yaml"
            if not config_path.exists():
                has_config = False
                logger.error(f"Could not find config path: {config_path}")

        if has_config:
            logger.info(f"Loading training config file from {config_path}")
            with open(config_path) as file:
                train_config = OmegaConf.load(file)

            if train_config.eval_overrides is not None:
                train_config = OmegaConf.merge(
                    train_config, train_config.eval_overrides
                )
            config = OmegaConf.merge(train_config, override_config)
            # print(config)
        else:
            config = override_config
    else:
        if override_config.eval_overrides is not None:
            config = override_config.copy()
            eval_overrides = OmegaConf.to_container(config.eval_overrides, resolve=True)
            for arg in sys.argv[1:]:
                if not arg.startswith("+"):
                    key = arg.split("=")[0]
                    if key in eval_overrides:
                        del eval_overrides[key]
            config.eval_overrides = OmegaConf.create(eval_overrides)
            config = OmegaConf.merge(config, eval_overrides)
        else:
            config = override_config
            
    simulator_type = config.simulator['_target_'].split('.')[-1]
    if simulator_type == 'IsaacSim':
        from omni.isaac.lab.app import AppLauncher
        import argparse
        parser = argparse.ArgumentParser(description="Train an RL agent with RSL-RL.")
        parser.add_argument("--num_envs", type=int, default=1, help="Number of environments to simulate.")
        parser.add_argument("--seed", type=int, default=None, help="Seed used for the environment")
        parser.add_argument("--env_spacing", type=int, default=20, help="Distance between environments in simulator.")
        parser.add_argument("--output_dir", type=str, default="logs", help="Directory to store the training output.")
        AppLauncher.add_app_launcher_args(parser)

        # Parse known arguments to get argparse params
        args_cli, hydra_args = parser.parse_known_args()

        app_launcher = AppLauncher(args_cli)
        simulation_app = app_launcher.app
        print('args_cli', args_cli)
        print('hydra_args', hydra_args)
        sys.argv = [sys.argv[0]] + hydra_args
    if simulator_type == 'IsaacGym':
        import isaacgym
        
        
    print ("playback file import correctly")
    
    # from humanoidverse.agents.base_algo.base_algo import BaseAlgo  # noqa: E402
    from humanoidverse.utils.helpers import pre_process_config
    
    import torch
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    
    pre_process_config(config)
    # eval_log_dir = Path(config.eval_log_dir)
    # eval_log_dir.mkdir(parents=True, exist_ok=True)
    # 
    # logger.info(f"Saving eval logs to {eval_log_dir}")
    # with open(eval_log_dir / "config.yaml", "w") as file:
    #     OmegaConf.save(config, file)
    # 
    # print ("playback file dir created")

    # (no need for rendering)
    # ckpt_num = config.checkpoint.split('/')[-1].split('_')[-1].split('.')[0]
    # config.env.config.save_rendering_dir = str(checkpoint.parent / "renderings" / f"ckpt_{ckpt_num}")
    # config.env.config.ckpt_dir = str(checkpoint.parent) # commented out for now, might need it back to save motion
    
    # print(config)
    
    config.env.config.save_rendering_dir = str(play.parent / "renderings" / f"ckpt_play")   # dummy dir for test only

    env = instantiate(config.env, device=device)
    
    print("load the env")

    # checkpoint_path = str(checkpoint)
    # checkpoint_dir = os.path.dirname(checkpoint_path)

    # from checkpoint path (no need for export)

    # ROBOVERSE_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    # exported_policy_path = os.path.join(ROBOVERSE_ROOT_DIR, checkpoint_dir, 'exported')
    # os.makedirs(exported_policy_path, exist_ok=True)
    # exported_policy_name = checkpoint_path.split('/')[-1]
    # exported_onnx_name = exported_policy_name.replace('.pt', '.onnx')
    
    from humanoidverse.agents.base_algo.base_algo import BaseAlgo  # noqa: E402
    algo: BaseAlgo = instantiate(config.algo, env=env, device=device, log_dir=None)
    algo.setup()
    
    algo.evaluate_with_action_sequence("/home/lixingfang/Project/HumanoidVerse/logs/G1TestDeploy/20250730_105719-G112dof_loco_IsaacGym-locomotion-g1_12dof/model_playback_5000.npz")
    
if __name__ == "__main__":
    main()
