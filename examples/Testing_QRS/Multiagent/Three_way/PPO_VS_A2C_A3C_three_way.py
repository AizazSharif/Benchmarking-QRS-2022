#!/bin/env python
import gym
import macad_gym  # noqa F401
import argparse
import os
from pprint import pprint

import cv2
import ray
import ray.tune as tune
from gym.spaces import Box, Discrete
from macad_agents.rllib.env_wrappers import wrap_deepmind
from macad_agents.rllib.models import register_mnih15_net

import datetime
import json
from ray.rllib.agents.ppo import ppo
from ray.rllib.agents.a3c import a2c
from ray.rllib.agents.a3c import a3c
# from ray.rllib.agents.pg import pg
from ray.rllib.agents.impala import impala
from ray.rllib.agents.dqn import dqn


from ray.rllib.agents.ppo.ppo_tf_policy import PPOTFPolicy #0.8.5
from ray.rllib.agents.a3c.a2c import A3CTFPolicy #0.8.5
from ray.rllib.agents.a3c.a3c_tf_policy import A3CTFPolicy #0.8.5



from ray.rllib.models.catalog import ModelCatalog
from ray.rllib.models.preprocessors import Preprocessor
from ray.tune import register_env
import time
from pprint import pprint
import pickle
from tqdm import tqdm
import tensorflow as tf
tf.compat.v1.disable_eager_execution()

from tensorboardX import SummaryWriter
timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
writer = SummaryWriter("logss/" + timestamp)

# from tensorflow.compat.v1 import ConfigProto
# from tensorflow.compat.v1 import InteractiveSession
# config = tf.ConfigProto()
# config.gpu_options.allow_growth = True
# session = InteractiveSession(config=config)

# config = tf.ConfigProto()
# config.gpu_options.per_process_gpu_memory_fraction = 0.7
# tf.keras.backend.set_session(tf.Session(config=config));

try:
    from ray.rllib.agents.agent import get_agent_class
except ImportError:
    from ray.rllib.agents.registry import get_agent_class

from ray.rllib.agents.trainer_template import build_trainer



parser = argparse.ArgumentParser()
parser.add_argument(
    "--env",
    default="PongNoFrameskip-v4",
    help="Name Gym env. Used only in debug mode. Default=PongNoFrameskip-v4")
parser.add_argument(
    "--checkpoint-path",
    #Replace it with your path of last training checkpoints
    default='/home/aizaz/Desktop/PhD-20210325T090933Z-001/PhD/10_August_2022/Benchmarking-Archive/examples/Training_QRS/A2C/Three_way/A2C_Three_way/A2C_A2C_three_way_train-v0_0_2022-08-18_11-15-38bhnv4e56/checkpoint_50/checkpoint-50',
    help="Path to checkpoint to resume training")
parser.add_argument(
    "--checkpoint-path2",
    #Replace it with your path of last training checkpoints
    default='/home/aizaz/Desktop/PhD-20210325T090933Z-001/PhD/10_August_2022/Benchmarking-Archive/examples/Training_QRS/A2C/Straight/A2C_Straight/A2C_A2C_straight_train-v0_0_2022-08-17_10-38-521u2w1itn/checkpoint_50/checkpoint-50',
    help="Path to checkpoint to resume training")
parser.add_argument(
    "--checkpoint-path3",
    #Replace it with your path of last training checkpoints
    default='/home/aizaz/Desktop/PhD-20210325T090933Z-001/PhD/10_August_2022/Benchmarking-Archive/examples/Training_QRS/A3C/Three_way/A3C_Three_way/A3C_A3C_three_way_train-v0_0_2022-08-18_08-45-236r1loxiv/checkpoint_50/checkpoint-50',
    help="Path to checkpoint to resume training")
# parser.add_argument(
#     "--checkpoint-path4",
#     #Replace it with your path of last training checkpoints
#     default='/home/aizaz/ray_results/PG_Training/MA-Inde-PG-SSI3CCARLA/PG_HomoNcomIndePOIntrxMASS3CTWN3-v0_0_2021-09-06_21-32-04j9c0o62i/checkpoint_17/checkpoint-17',
#     help="Path to checkpoint to resume training")
parser.add_argument(
    "--disable-comet",
    action="store_true",
    help="Disables comet logging. Used for local smoke tests")
parser.add_argument(
    "--num-workers",
    default=1, #2
    type=int,
    help="Num workers (CPU cores) to use")
parser.add_argument(
    "--num-gpus", default=1, type=int, help="Number of gpus to use. Default=2")
parser.add_argument(
    "--sample-bs-per-worker",
    default=1024,
    type=int,
    help="Number of samples in a batch per worker. Default=50")
parser.add_argument(
    "--train-bs",
    default=128,
    type=int,
    help="Train batch size. Use as per available GPU mem. Default=500")
parser.add_argument(
    "--envs-per-worker",
    default=1,
    type=int,
    help="Number of env instances per worker. Default=10")
parser.add_argument(
    "--notes",
    default=None,
    help="Custom experiment description to be added to comet logs")
parser.add_argument(
    "--model-arch",
    default="mnih15",
    help="Model architecture to use. Default=mnih15")
parser.add_argument(
    "--num-steps",
    default=200, 
    type=int,
    help="Number of steps to train. Default=20M")
parser.add_argument(
    "--num-iters",
    default=1, #20
    type=int,
    help="Number of training iterations. Default=20")
parser.add_argument(
    "--log-graph",
    action="store_true",
    help="Write TF graph on Tensorboard for debugging")
parser.add_argument(
    "--num-framestack",
    type=int,
    default=4,
    help="Number of obs frames to stack")
parser.add_argument(
    "--redis-address",
    default=None,
    help="Address of ray head node. Be sure to start ray with"
    "ray start --redis-address <...> --num-gpus<.> before running this script")
parser.add_argument(
    "--use-lstm", action="store_true", help="Append a LSTM cell to the model")

args = parser.parse_args()

#--------------------------------------------------------------------
model_name = args.model_arch
if model_name == "mnih15":
    register_mnih15_net()  # Registers mnih15
else:
    print("Unsupported model arch. Using default")
    register_mnih15_net()
    model_name = "mnih15"

# Used only in debug mode
env_name = "PPO_three_way_train-v0"
env = gym.make(env_name)
env_actor_configs = env.configs
num_framestack = args.num_framestack
# env_config["env"]["render"] = False

# Used only in debug mode
env_name_2 = "A2C_three_way_train-v0"
env_2 = gym.make(env_name_2)
env_actor_configs_2 = env_2.configs
# num_framestack = args.num_framestack
# env_config["env"]["render"] = False

# Used only in debug mode
env_name_3 = "A3C_three_way_train-v0"
env_3 = gym.make(env_name_3)
env_actor_configs_3 = env_3.configs
# num_framestack = args.num_framestack
# env_config["env"]["render"] = False

# Used only in debug mode
# env_name_4 = "UrbanPGTraining-v0"
# env_4 = gym.make(env_name_4)
# env_actor_configs_4 = env_4.configs
# num_framestack = args.num_framestack
# env_config["env"]["render"] = False

# # Used only in debug mode
# env_name_5 = "UrbanIMPALATraining-v0"
# env_5 = gym.make(env_name_5)
# env_actor_configs_5 = env_5.configs
# # num_framestack = args.num_framestack
# # env_config["env"]["render"] = False

# # Used only in debug mode
# env_name_6 = "UrbanDQNTraining-v0"
# env_6 = gym.make(env_name_6)
# env_actor_configs_6 = env_6.configs
# # num_framestack = args.num_framestack
# # env_config["env"]["render"] = False

# Used only in debug mode
env_name_7 = "PPO_A2C_A3C_three_way_train-v0"
env_7 = gym.make(env_name_7)
env_actor_configs_7 = env_7.configs
# num_framestack = args.num_framestack
# env_config["env"]["render"] = False

#--------------------------------------------------------------------

def env_creator(env_config):
    # NOTES: env_config.worker_index & vector_index are useful for
    # curriculum learning or joint training experiments
    import macad_gym
    env = gym.make("PPO_three_way_train-v0")

    # Apply wrappers to: convert to Grayscale, resize to 84 x 84,
    # stack frames & some more op
    env = wrap_deepmind(env, dim=84, num_framestack=num_framestack)
    return env

def env_creator_2(env_config):
    # NOTES: env_config.worker_index & vector_index are useful for
    # curriculum learning or joint training experiments
    import macad_gym
    env = gym.make("A2C_three_way_train-v0")

    # Apply wrappers to: convert to Grayscale, resize to 84 x 84,
    # stack frames & some more op
    env = wrap_deepmind(env, dim=84, num_framestack=num_framestack)
    return env

def env_creator_3(env_config):
    # NOTES: env_config.worker_index & vector_index are useful for
    # curriculum learning or joint training experiments
    import macad_gym
    env = gym.make("A3C_three_way_train-v0")

    # Apply wrappers to: convert to Grayscale, resize to 84 x 84,
    # stack frames & some more op
    env = wrap_deepmind(env, dim=84, num_framestack=num_framestack)
    return env

# def env_creator_4(env_config):
#     # NOTES: env_config.worker_index & vector_index are useful for
#     # curriculum learning or joint training experiments
#     import macad_gym
#     env = gym.make("UrbanPGTraining-v0")

    # Apply wrappers to: convert to Grayscale, resize to 84 x 84,
    # stack frames & some more op
    env = wrap_deepmind(env, dim=84, num_framestack=num_framestack)
    return env
# def env_creator_5(env_config):
#     # NOTES: env_config.worker_index & vector_index are useful for
#     # curriculum learning or joint training experiments
#     import macad_gym
#     env = gym.make("UrbanIMPALATraining-v0")

#     # Apply wrappers to: convert to Grayscale, resize to 84 x 84,
#     # stack frames & some more op
#     env = wrap_deepmind(env, dim=84, num_framestack=num_framestack)
#     return env
# def env_creator_6(env_config):
#     # NOTES: env_config.worker_index & vector_index are useful for
#     # curriculum learning or joint training experiments
#     import macad_gym
#     env = gym.make("UrbanDQNTraining-v0")

#     # Apply wrappers to: convert to Grayscale, resize to 84 x 84,
#     # stack frames & some more op
#     env = wrap_deepmind(env, dim=84, num_framestack=num_framestack)
#     return env           

def env_creator_7(env_config):
    # NOTES: env_config.worker_index & vector_index are useful for
    # curriculum learning or joint training experiments
    import macad_gym
    env = gym.make("PPO_A2C_A3C_three_way_train-v0")

    # Apply wrappers to: convert to Grayscale, resize to 84 x 84,
    # stack frames & some more op
    env = wrap_deepmind(env, dim=84, num_framestack=num_framestack)
    return env

register_env(env_name, lambda config: env_creator(config))
register_env(env_name_2, lambda config: env_creator_2(config))
register_env(env_name_3, lambda config: env_creator_3(config))
# register_env(env_name_4, lambda config: env_creator_4(config))
# register_env(env_name_5, lambda config: env_creator_5(config))
# register_env(env_name_6, lambda config: env_creator_6(config))
register_env(env_name_7, lambda config: env_creator_7(config))

#--------------------------------------------------------------------

# Placeholder to enable use of a custom pre-processor
class ImagePreproc(Preprocessor):
    def _init_shape(self, obs_space, options):
        self.shape = (84, 84, 3)  # Adjust third dim if stacking frames
        return self.shape

    def transform(self, observation):
        observation = cv2.resize(observation, (self.shape[0], self.shape[1]))
        return observation
def transform(self, observation):
        observation = cv2.resize(observation, (self.shape[0], self.shape[1]))
        return observation

ModelCatalog.register_custom_preprocessor("sq_im_84", ImagePreproc)
#--------------------------------------------------------------------

if args.redis_address is not None:
    # num_gpus (& num_cpus) must not be provided when connecting to an
    # existing cluster
    ray.init(redis_address=args.redis_address,lru_evict=True, log_to_driver=False)
else:
    ray.init(num_gpus=args.num_gpus,lru_evict=True, log_to_driver=False)

config = {
    # Model and preprocessor options.
    "model": {
        "custom_model": model_name,
        "custom_options": {
            # Custom notes for the experiment
            "notes": {
                "args": vars(args)
            },
        },
        # NOTE:Wrappers are applied by RLlib if custom_preproc is NOT specified
        "custom_preprocessor": "sq_im_84",
        "dim": 84,
        "free_log_std": False,  # if args.discrete_actions else True,
        "grayscale": True,
        # conv_filters to be used with the custom CNN model.
        # "conv_filters": [[16, [4, 4], 2], [32, [3, 3], 2], [16, [3, 3], 2]]
    },
    # preproc_pref is ignored if custom_preproc is specified
    # "preprocessor_pref": "deepmind",

    # env_config to be passed to env_creator
    
    "env_config": env_actor_configs
}

def default_policy():
    env_actor_configs["env"]["render"] = False

    config = {
    # Model and preprocessor options.
    "model": {
        "custom_model": model_name,
        "custom_options": {
            # Custom notes for the experiment
            "notes": {
                "args": vars(args)
            },
        },
        # NOTE:Wrappers are applied by RLlib if custom_preproc is NOT specified
        "custom_preprocessor": "sq_im_84",
        "dim": 84,
        "free_log_std": False,  # if args.discrete_actions else True,
        "grayscale": True,
        # conv_filters to be used with the custom CNN model.
        # "conv_filters": [[16, [4, 4], 2], [32, [3, 3], 2], [16, [3, 3], 2]]
    },


    # Should use a critic as a baseline (otherwise don't use value baseline;
    # required for using GAE).
    "use_critic": True,
    # If true, use the Generalized Advantage Estimator (GAE)
    # with a value function, see https://arxiv.org/pdf/1506.02438.pdf.
    "use_gae": True,
    # The GAE(lambda) parameter.
    "lambda": 1.0,
    # Initial coefficient for KL divergence.
    "kl_coeff": 0.3,
    # Size of batches collected from each worker.
    # "rollout_fragment_length": 128,
    # Number of timesteps collected for each SGD round. This defines the size
    # of each SGD epoch.
    # "train_batch_size": 4000,
    # Total SGD batch size across all devices for SGD. This defines the
    # minibatch size within each epoch.
    "sgd_minibatch_size": 64,
    # Whether to shuffle sequences in the batch when training (recommended).
    "shuffle_sequences": True,
    # Number of SGD iterations in each outer loop (i.e., number of epochs to
    # execute per train batch).
    "num_sgd_iter": 8,
    # Stepsize of SGD.
    "lr": 5e-5,
    # Learning rate schedule.
    # "lr_schedule": None,
    # Share layers for value function. If you set this to True, it's important
    # to tune vf_loss_coeff.
    "vf_share_layers": False,
    # Coefficient of the value function loss. IMPORTANT: you must tune this if
    # you set vf_share_layers: True.
    "vf_loss_coeff": 1.0,
    # Coefficient of the entropy regularizer.
    "entropy_coeff": 0.1,
    # Decay schedule for the entropy regularizer.
    "entropy_coeff_schedule": None,
    # PPO clip parameter.
    "clip_param": 0.3,
    # Clip param for the value function. Note that this is sensitive to the
    # scale of the rewards. If your expected V is large, increase this.
    "vf_clip_param": 10.0,
    # If specified, clip the global norm of gradients by this amount.
    "grad_clip": None,
    # Target value for KL divergence.
    "kl_target": 0.03,
    # Whether to rollout "complete_episodes" or "truncate_episodes".
    "batch_mode": "complete_episodes",
    # Which observation filter to apply to the observation.
    "observation_filter": "NoFilter",
    # Uses the sync samples optimizer instead of the multi-gpu one. This is
    # usually slower, but you might want to try it if you run into issues with
    # the default optimizer.
    "simple_optimizer": False,
    # Use PyTorch as framework?
    "use_pytorch": False,

    # Discount factor of the MDP.
    "gamma": 0.99,
    # Number of steps after which the episode is forced to terminate. Defaults
    # to `env.spec.max_episode_steps` (if present) for Gym envs.
    "horizon": 1024,
    # Calculate rewards but don't reset the environment when the horizon is
    # hit. This allows value estimation and RNN state to span across logical
    # episodes denoted by horizon. This only has an effect if horizon != inf.
    "soft_horizon": True,
    # Don't set 'done' at the end of the episode. Note that you still need to
    # set this if soft_horizon=True, unless your env is actually running
    # forever without returning done=True.
    "no_done_at_end": True,
    "monitor": False,




    # System params.
    # Should be divisible by num_envs_per_worker
    "sample_batch_size":
     args.sample_bs_per_worker,
    "train_batch_size":
    args.train_bs,
    # "rollout_fragment_length": 128,
    "num_workers":
    args.num_workers,
    # Number of environments to evaluate vectorwise per worker.
    "num_envs_per_worker":
    args.envs_per_worker,
    "num_cpus_per_worker":
    1,
    "num_gpus_per_worker":
    1,
    # "eager_tracing": True,

    # # Learning params.
    # "grad_clip":
    # 40.0,
    # "clip_rewards":
    # True,
    # either "adam" or "rmsprop"
    "opt_type":
    "adam",
    # "lr":
    # 0.003,
    "lr_schedule": [
        [0, 0.0006],
        [20000000, 0.000000000001],  # Anneal linearly to 0 from start 2 end
    ],
    # rmsprop considered
    "decay":
    0.5,
    "momentum":
    0.0,
    "epsilon":
    0.1,
    # # balancing the three losses
    # "vf_loss_coeff":
    # 0.5,  # Baseline loss scaling
    # "entropy_coeff":
    # -0.01,

    # preproc_pref is ignored if custom_preproc is specified
    # "preprocessor_pref": "deepmind",
   # "gamma": 0.99,

    "use_lstm": args.use_lstm,
    # env_config to be passed to env_creator
    "env":{
        "render": True
    },
    # "in_evaluation": True,
    # "evaluation_num_episodes": 1,
    "env_config": env_actor_configs
    }


    # pprint (config)
    return (PPOTFPolicy, Box(0.0, 255.0, shape=(84, 84, 3)), Discrete(9),config)

config_2 = {
    # Model and preprocessor options.
    "model": {
        "custom_model": model_name,
        "custom_options": {
            # Custom notes for the experiment
            "notes": {
                "args": vars(args)
            },
        },
        # NOTE:Wrappers are applied by RLlib if custom_preproc is NOT specified
        "custom_preprocessor": "sq_im_84",
        "dim": 84,
        "free_log_std": False,  # if args.discrete_actions else True,
        "grayscale": True,
        # conv_filters to be used with the custom CNN model.
        # "conv_filters": [[16, [4, 4], 2], [32, [3, 3], 2], [16, [3, 3], 2]]
    },
    # preproc_pref is ignored if custom_preproc is specified
    # "preprocessor_pref": "deepmind",

    # env_config to be passed to env_creator
    
    "env_config": env_actor_configs_2
}

def default_policy_2():
    env_actor_configs_2["env"]["render"] = False

    config_2 = {
    # Model and preprocessor options.
    "model": {
        "custom_model": model_name,
        "custom_options": {
            # Custom notes for the experiment
            "notes": {
                "args": vars(args)
            },
        },
        # NOTE:Wrappers are applied by RLlib if custom_preproc is NOT specified
        "custom_preprocessor": "sq_im_84",
        "dim": 84,
        "free_log_std": False,  # if args.discrete_actions else True,
        "grayscale": True,
        # conv_filters to be used with the custom CNN model.
        # "conv_filters": [[16, [4, 4], 2], [32, [3, 3], 2], [16, [3, 3], 2]]
    },


    # Should use a critic as a baseline (otherwise don't use value baseline;
    # required for using GAE).
    "use_critic": True,
    # If true, use the Generalized Advantage Estimator (GAE)
    # with a value function, see https://arxiv.org/pdf/1506.02438.pdf.
    "use_gae": True,
    # Size of rollout batch
    # "rollout_fragment_length": 10,
    # GAE(gamma) parameter
    "lambda": 1.0,
    # Max global norm for each gradient calculated by worker
    "grad_clip": 40.0,
    # Learning rate
    "lr": 0.0001,
    # Learning rate schedule
    "lr_schedule": None,
    # Value Function Loss coefficient
    "vf_loss_coeff": 0.5,
    # Entropy coefficient
    "entropy_coeff": 0.01,
    # Min time per iteration
    "min_iter_time_s": 5,
    # Workers sample async. Note that this increases the effective
    # rollout_fragment_length by up to 5x due to async buffering of batches.
    "sample_async": True,

    # Discount factor of the MDP.
    "gamma": 0.99,
    # Number of steps after which the episode is forced to terminate. Defaults
    # to `env.spec.max_episode_steps` (if present) for Gym envs.
    "horizon": 1024,
    # Calculate rewards but don't reset the environment when the horizon is
    # hit. This allows value estimation and RNN state to span across logical
    # episodes denoted by horizon. This only has an effect if horizon != inf.
    "soft_horizon": True,
    # Don't set 'done' at the end of the episode. Note that you still need to
    # set this if soft_horizon=True, unless your env is actually running
    # forever without returning done=True.
    "no_done_at_end": True,
    "monitor": True,




    # System params.
    # Should be divisible by num_envs_per_worker
    "sample_batch_size":
     args.sample_bs_per_worker,
    "train_batch_size":
    args.train_bs,
    # "rollout_fragment_length": 128,
    "num_workers":
    args.num_workers,
    # Number of environments to evaluate vectorwise per worker.
    "num_envs_per_worker":
    args.envs_per_worker,
    "num_cpus_per_worker":
    1,
    "num_gpus_per_worker":
    1,
    # "eager_tracing": True,

    # # Learning params.
    # "grad_clip":
    # 40.0,
    # "clip_rewards":
    # True,
    # either "adam" or "rmsprop"
    "opt_type":
    "adam",
    # "lr":
    # 0.003,
    "lr_schedule": [
        [0, 0.0006],
        [20000000, 0.000000000001],  # Anneal linearly to 0 from start 2 end
    ],
    # rmsprop considered
    "decay":
    0.5,
    "momentum":
    0.0,
    "epsilon":
    0.1,
    # # balancing the three losses
    # "vf_loss_coeff":
    # 0.5,  # Baseline loss scaling
    # "entropy_coeff":
    # -0.01,

    # preproc_pref is ignored if custom_preproc is specified
    # "preprocessor_pref": "deepmind",
   # "gamma": 0.99,

    "use_lstm": args.use_lstm,
    # env_config to be passed to env_creator
    "env":{
        "render": True
    },
    # "in_evaluation": True,
    # "evaluation_num_episodes": 1,
    "env_config": env_actor_configs_2
    }






    # pprint (config)
    return (A3CTFPolicy, Box(0.0, 255.0, shape=(84, 84, 3)), Discrete(9),config_2)


config_3 = {
    # Model and preprocessor options.
    "model": {
        "custom_model": model_name,
        "custom_options": {
            # Custom notes for the experiment
            "notes": {
                "args": vars(args)
            },
        },
        # NOTE:Wrappers are applied by RLlib if custom_preproc is NOT specified
        "custom_preprocessor": "sq_im_84",
        "dim": 84,
        "free_log_std": False,  # if args.discrete_actions else True,
        "grayscale": True,
        # conv_filters to be used with the custom CNN model.
        # "conv_filters": [[16, [4, 4], 2], [32, [3, 3], 2], [16, [3, 3], 2]]
    },
    # preproc_pref is ignored if custom_preproc is specified
    # "preprocessor_pref": "deepmind",

    # env_config to be passed to env_creator
    
    "env_config": env_actor_configs_3
}

def default_policy_3():
    env_actor_configs_3["env"]["render"] = False

    config_3 = {
    # Model and preprocessor options.
    "model": {
        "custom_model": model_name,
        "custom_options": {
            # Custom notes for the experiment
            "notes": {
                "args": vars(args)
            },
        },
        # NOTE:Wrappers are applied by RLlib if custom_preproc is NOT specified
        "custom_preprocessor": "sq_im_84",
        "dim": 84,
        "free_log_std": False,  # if args.discrete_actions else True,
        "grayscale": True,
        # conv_filters to be used with the custom CNN model.
        # "conv_filters": [[16, [4, 4], 2], [32, [3, 3], 2], [16, [3, 3], 2]]
    },


    # Should use a critic as a baseline (otherwise don't use value baseline;
    # required for using GAE).
    "use_critic": True,
    # If true, use the Generalized Advantage Estimator (GAE)
    # with a value function, see https://arxiv.org/pdf/1506.02438.pdf.
    "use_gae": True,
    # Size of rollout batch
    "rollout_fragment_length": 10,
    # GAE(gamma) parameter
    "lambda": 1.0,
    # Max global norm for each gradient calculated by worker
    "grad_clip": 40.0,
    "epsilon":
    0.1,
    # Learning rate
    "lr": 0.0001,
    # Learning rate schedule
    "lr_schedule": None,
    # Value Function Loss coefficient
    "vf_loss_coeff": 0.5,
    # Entropy coefficient
    "entropy_coeff": 0.01,
    # Min time per iteration
    "min_iter_time_s": 5,
    # Workers sample async. Note that this increases the effective
    # rollout_fragment_length by up to 5x due to async buffering of batches.
    "sample_async": True,

    # Discount factor of the MDP.
    "gamma": 0.9,
    # Number of steps after which the episode is forced to terminate. Defaults
    # to `env.spec.max_episode_steps` (if present) for Gym envs.
    "horizon": 1024,
    # Calculate rewards but don't reset the environment when the horizon is
    # hit. This allows value estimation and RNN state to span across logical
    # episodes denoted by horizon. This only has an effect if horizon != inf.
    "soft_horizon": True,
    # Don't set 'done' at the end of the episode. Note that you still need to
    # set this if soft_horizon=True, unless your env is actually running
    # forever without returning done=True.
    "no_done_at_end": True,
    "monitor": True,




    # System params.
    # Should be divisible by num_envs_per_worker
    "sample_batch_size":
     args.sample_bs_per_worker,
    "train_batch_size":
    args.train_bs,
    # "rollout_fragment_length": 128,
    "num_workers":
    args.num_workers,
    # Number of environments to evaluate vectorwise per worker.
    "num_envs_per_worker":
    args.envs_per_worker,
    "num_cpus_per_worker":
    1,
    "num_gpus_per_worker":
    1,
    # "eager_tracing": True,

    # # Learning params.
    # "grad_clip":
    # 40.0,
    # "clip_rewards":
    # True,
    # either "adam" or "rmsprop"
    "opt_type":
    "adam",
    # "lr":
    # 0.003,
    "lr_schedule": [
        [0, 0.0006],
        [20000000, 0.000000000001],  # Anneal linearly to 0 from start 2 end
    ],
    # rmsprop considered
    "decay":
    0.5,
    "momentum":
    0.0,

    # # balancing the three losses
    # "vf_loss_coeff":
    # 0.5,  # Baseline loss scaling
    # "entropy_coeff":
    # -0.01,

    # preproc_pref is ignored if custom_preproc is specified
    # "preprocessor_pref": "deepmind",
   # "gamma": 0.99,

    "use_lstm": args.use_lstm,
    # env_config to be passed to env_creator
    "env":{
        "render": True
    },
    # "in_evaluation": True,
    # "evaluation_num_episodes": 1,
    "env_config": env_actor_configs_3
    }






    # pprint (config)
    return (A3CTFPolicy, Box(0.0, 255.0, shape=(84, 84, 3)), Discrete(9),config_3)












def update_checkpoint_for_rollout(checkpoint_path):
    with open(checkpoint_path, "rb") as f:
        extra_data = pickle.load(f)
    if not "trainer_state" in extra_data:
        extra_data["trainer_state"] = {}
        with open(checkpoint_path, 'wb') as f:
            pickle.dump(extra_data, f)

# update_checkpoint_for_rollout(args.checkpoint_path)
# update_checkpoint_for_rollout(args.checkpoint_path2)
# update_checkpoint_for_rollout(args.checkpoint_path3)
# update_checkpoint_for_rollout(args.checkpoint_path4)
# update_checkpoint_for_rollout(args.checkpoint_path5)
# update_checkpoint_for_rollout(args.checkpoint_path6)

# pprint (args.checkpoint_path)
# pprint(os.path.isfile(args.checkpoint_path))
# pprint (args.checkpoint_path2)
# pprint(os.path.isfile(args.checkpoint_path2))
# pprint (args.checkpoint_path3)
# pprint(os.path.isfile(args.checkpoint_path3))
# pprint (args.checkpoint_path4)
# pprint(os.path.isfile(args.checkpoint_path4))
# pprint (args.checkpoint_path5)
# pprint(os.path.isfile(args.checkpoint_path5))
# pprint (args.checkpoint_path6)
# pprint(os.path.isfile(args.checkpoint_path6))



#--------------------------------------------------------------------
multiagent = True

MyTrainer = build_trainer(
        name="MultiAgent",
        default_policy=None)
# Create a new dummy Trainer to "fix" our checkpoint.
# new_trainer = ppo.PPOTrainer(
#     env=env_name,
#     # Use independent policy graphs for each agent
#     config={

#         "multiagent": {
#             "policies": {
#                 id: default_policy()
#                 for id in env_actor_configs["actors"].keys()
#             },
#             "policy_mapping_fn": lambda agent_id: agent_id,
#         },
#         "env_config": env_actor_configs,
#         "num_workers": args.num_workers,
#         "num_envs_per_worker": args.envs_per_worker,
#         "sample_batch_size": args.sample_bs_per_worker,
#         # "rollout_fragment_length": args.sample_bs_per_worker,

#         "train_batch_size": args.train_bs,
 
#     })

# # Get untrained weights for all policies.
# untrained_weights = new_trainer.get_weights()
# # Restore all policies from checkpoint.
# new_trainer.restore(args.checkpoint_path)
# # Set back all weights (except for 1st agent) to original
# # untrained weights.
# new_trainer.set_weights(
#     {pid: w
#      for pid, w in untrained_weights.items() if pid != "car2PPO"})

# #-------------------------------------------------------------------
# # Create a new dummy Trainer to "fix" our checkpoint.
# new_trainer_2 = a2c.A2CTrainer(
#     env=env_name_2,
#     # Use independent policy graphs for each agent
#     config={

#         "multiagent": {
#             "policies": {
#                 id: default_policy_2()
#                 for id in env_actor_configs_2["actors"].keys()
#             },
#             "policy_mapping_fn": lambda agent_id: agent_id,
#         },
#         "env_config": env_actor_configs_2,
#         "num_workers": args.num_workers,
#         "num_envs_per_worker": args.envs_per_worker,
#         "sample_batch_size": args.sample_bs_per_worker,
#         "rollout_fragment_length": args.sample_bs_per_worker,

#         "train_batch_size": args.train_bs,
 
#     })

# # Get untrained weights for all policies.
# untrained_weights_2 = new_trainer_2.get_weights()
# # Restore all policies from checkpoint.
# new_trainer_2.restore(args.checkpoint_path2)
# # Set back all weights (except for 1st agent) to original
# # untrained weights.
# new_trainer_2.set_weights(
#     {pid: w
#      for pid, w in untrained_weights_2.items() if pid != "car2A2C"})


# #-------------------------------------------------------------------
# # Create a new dummy Trainer to "fix" our checkpoint.
# new_trainer_3 = a2c.A2CTrainer(
#     env=env_name_3,
#     # Use independent policy graphs for each agent
#     config={

#         "multiagent": {
#             "policies": {
#                 id: default_policy_3()
#                 for id in env_actor_configs_3["actors"].keys()
#             },
#             "policy_mapping_fn": lambda agent_id: agent_id,
#         },
        
#         "env_config": env_actor_configs_3,
#         "num_workers": args.num_workers,
#         "num_envs_per_worker": args.envs_per_worker,
#         "sample_batch_size": args.sample_bs_per_worker,
#         "rollout_fragment_length": args.sample_bs_per_worker,

#         "train_batch_size": args.train_bs,
 
#     })

# # Get untrained weights for all policies.
# untrained_weights_3 = new_trainer_3.get_weights()
# # Restore all policies from checkpoint.
# new_trainer_3.restore(args.checkpoint_path3)
# # Set back all weights (except for 1st agent) to original
# # untrained weights.
# new_trainer_3.set_weights(
#     {pid: w
#      for pid, w in untrained_weights_3.items() if pid != "car2A3C"})     

# #-------------------------------------------------------------------
# # Create a new dummy Trainer to "fix" our checkpoint.
# new_trainer_4 = pg.PGTrainer(
#     env=env_name_4,
#     # Use independent policy graphs for each agent
#     config={

#         "multiagent": {
#             "policies": {
#                 id: default_policy_4()
#                 for id in env_actor_configs_4["actors"].keys()
#             },
#             "policy_mapping_fn": lambda agent_id: agent_id,
#         },
#         "env_config": env_actor_configs_4,
#         "num_workers": args.num_workers,
#         "num_envs_per_worker": args.envs_per_worker,
#         "sample_batch_size": args.sample_bs_per_worker,
#         "rollout_fragment_length": args.sample_bs_per_worker,

#         "train_batch_size": args.train_bs,
 
#     })

# # Get untrained weights for all policies.
# untrained_weights_4 = new_trainer_4.get_weights()
# # Restore all policies from checkpoint.
# new_trainer_4.restore(args.checkpoint_path4)
# # Set back all weights (except for 1st agent) to original
# # untrained weights.
# new_trainer_4.set_weights(
#     {pid: w
#      for pid, w in untrained_weights_4.items() if pid != "car2PG"})     


# #-------------------------------------------------------------------
# # Create a new dummy Trainer to "fix" our checkpoint.
# new_trainer_6 = dqn.DQNTrainer(
#     env=env_name_6,
#     # Use independent policy graphs for each agent
#     config={

#         "multiagent": {
#             "policies": {
#                 id: default_policy_6()
#                 for id in env_actor_configs_6["actors"].keys()
#             },
#             "policy_mapping_fn": lambda agent_id: agent_id,
#         },
#         "env_config": env_actor_configs_6,
#         "num_workers": args.num_workers,
#         "num_envs_per_worker": args.envs_per_worker,
#         "sample_batch_size": args.sample_bs_per_worker,
#         "rollout_fragment_length": args.sample_bs_per_worker,

#         "train_batch_size": args.train_bs,
 
#     })


# # Get untrained weights for all policies.
# untrained_weights_6 = new_trainer_6.get_weights()
# # Restore all policies from checkpoint.
# new_trainer_6.restore(args.checkpoint_path6)
# # Set back all weights (except for 1st agent) to original
# # untrained weights.
# new_trainer_6.set_weights(
#     {pid: w
#      for pid, w in untrained_weights_6.items() if pid != "car2DQN"})   

# #-------------------------------------------------------------------
# # Create a new dummy Trainer to "fix" our checkpoint.
# new_trainer_5 = impala.ImpalaAgent(
#     env=env_name_5,
#     # Use independent policy graphs for each agent
#     config={

#         "multiagent": {
#             "policies": {
#                 id: default_policy_5()
#                 for id in env_actor_configs_5["actors"].keys()
#             },
#             "policy_mapping_fn": lambda agent_id: agent_id,
#         },
#         "env_config": env_actor_configs_5,
#         "num_workers": args.num_workers,
#         "num_envs_per_worker": args.envs_per_worker,
#         "sample_batch_size": args.sample_bs_per_worker,
#         "rollout_fragment_length": args.sample_bs_per_worker,

#         "train_batch_size": args.train_bs,
 
#     })

# # Get untrained weights for all policies.
# untrained_weights_5 = new_trainer_5.get_weights()
# # Restore all policies from checkpoint.
# new_trainer_5.restore(args.checkpoint_path5)
# # Set back all weights (except for 1st agent) to original
# # untrained weights.
# new_trainer_5.set_weights(
#     {pid: w
#      for pid, w in untrained_weights_5.items() if pid != "car2IMPALA"})   





policies = {
        "carPPO": default_policy(),
        "carA2C": default_policy_2(),
        "carA3C": default_policy_3(),

        
    }



# experiment_spec = tune.Experiment(
#         "multi-carla/" + args.model_arch,
#         "PPO",
#         stop={"timesteps_since_restore": args.num_steps},
#         config=config,
#         resources_per_trial={
#             "cpu": 1,
#             "gpu": 1
#         })

experiment_spec = tune.run_experiments({
        "PPO-A2C-A3C-Three_way": {
            "run": MyTrainer,
            "env": env_name_7,
            "stop": {
                
                "training_iteration": args.num_iters,
                "timesteps_total": args.num_steps,
                "episodes_total": 1024,
                
            },

            "config": {

                "log_level": "DEBUG",
                # "num_sgd_iter": 10,  # Enables Experience Replay
                "multiagent": {
                    "policies": {"carPPO": default_policy(),
                        "carA2C": default_policy_2(),
                        "carA3C": default_policy_3(),
                   
                        # id: default_policy()
                        # for id in env_actor_configs["actors"].keys()
                    },
                    "policy_mapping_fn":
                    tune.function(lambda agent_id: agent_id),
                    "policies_to_train": ["carPPO","carA2C","carA3C"], #car2 and car3 are the victim Autonomous driving models
                },
                # "env_config": env_actor_configs,
                "num_workers": args.num_workers,
                "num_envs_per_worker": args.envs_per_worker,
                "sample_batch_size": args.sample_bs_per_worker,
                "train_batch_size": args.train_bs,
                #"horizon": 512, #yet to be fixed

            },
            "checkpoint_freq": 1,
            "checkpoint_at_end": True,


        }
    })


'''


#--------------------------------------------------------------------
agents_reward_dict = {}

obs = env.reset()
#for ep in range(2):
step = 0


episode_reward = 0
info_dict= []

agents_reward_dict = {'car1': 0.0, 'car2': 0.0, 'car3': 0.0}
done = False
i=0
action = {}
with open("info_car1_step.json", "w") as f1, open("info_car2.json", "w")  as f2, open("info_car3.json", "w")  as f3:
    print ("Starting a single episode for testing")
    while i < 2000:  # number of steps in a episodic run 
        i += 1
        for agent_id, agent_obs in obs.items():
            policy_id = trainer.config["multiagent"]["policy_mapping_fn"](agent_id)
            #pprint (policy_id)
            
            action[agent_id] = trainer.compute_action(agent_obs, policy_id=policy_id)
            #print (action[agent_id])
            #print (" -***************-- ")
        obs, reward, done, info = env.step(action)

        step += 1
        # sum up reward for all agents
        step_reward=0
        step_reward += reward["car2"]+reward["car3"]
        # step_reward = step_reward-reward["car1"]
        print ("Step reward : ",step_reward)
        writer.add_scalar("/step_reward_r", step_reward , step) 
        for agent_id in reward:
            agents_reward_dict[agent_id] += reward[agent_id]
            writer.add_scalar(agent_id + "/step_r",
                                  reward[agent_id], step)
               
            
            if agent_id=="car1":
                json.dump(info[agent_id], f1)
                f1.write("\n")
            if agent_id=="car2":
                json.dump(info[agent_id], f2)
                f2.write("\n")    
            if agent_id=="car3":
                json.dump(info[agent_id], f3)
                f3.write("\n")


        episode_reward += reward["car2"]+reward["car3"]
        # episode_reward = episode_reward-reward["car1"]
        print ("Episode reward : ",episode_reward)
        writer.add_scalar("/episode_reward_r", episode_reward , step) 
        pprint (" --- ")




print (" ====================== ======================= ")    


done = done['__all__']
env.close()
writer.close()

'''
ray.shutdown()
