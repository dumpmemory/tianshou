#!/usr/bin/env python3

import os
from collections.abc import Sequence
from typing import Literal

from sensai.util import logging
from sensai.util.logging import datetime_tag
from torch import nn

from examples.mujoco.mujoco_env import MujocoEnvFactory
from tianshou.highlevel.config import OnPolicyTrainingConfig
from tianshou.highlevel.experiment import (
    A2CExperimentBuilder,
    ExperimentConfig,
)
from tianshou.highlevel.params.algorithm_params import A2CParams
from tianshou.highlevel.params.lr_scheduler import LRSchedulerFactoryFactoryLinear
from tianshou.highlevel.params.optim import OptimizerFactoryFactoryRMSprop


def main(
    experiment_config: ExperimentConfig,
    task: str = "Ant-v4",
    buffer_size: int = 4096,
    hidden_sizes: Sequence[int] = (64, 64),
    lr: float = 7e-4,
    gamma: float = 0.99,
    epoch: int = 100,
    epoch_num_steps: int = 30000,
    collection_step_num_env_steps: int = 80,
    update_step_num_repetitions: int = 1,
    batch_size: int = 16,
    num_train_envs: int = 16,
    num_test_envs: int = 10,
    return_scaling: bool = True,
    vf_coef: float = 0.5,
    ent_coef: float = 0.01,
    gae_lambda: float = 0.95,
    bound_action_method: Literal["clip", "tanh"] = "clip",
    lr_decay: bool = True,
    max_grad_norm: float = 0.5,
) -> None:
    log_name = os.path.join(task, "a2c", str(experiment_config.seed), datetime_tag())

    training_config = OnPolicyTrainingConfig(
        max_epochs=epoch,
        epoch_num_steps=epoch_num_steps,
        batch_size=batch_size,
        num_train_envs=num_train_envs,
        num_test_envs=num_test_envs,
        buffer_size=buffer_size,
        collection_step_num_env_steps=collection_step_num_env_steps,
        update_step_num_repetitions=update_step_num_repetitions,
    )

    env_factory = MujocoEnvFactory(task, obs_norm=True)

    experiment = (
        A2CExperimentBuilder(env_factory, experiment_config, training_config)
        .with_a2c_params(
            A2CParams(
                gamma=gamma,
                gae_lambda=gae_lambda,
                action_bound_method=bound_action_method,
                return_scaling=return_scaling,
                ent_coef=ent_coef,
                vf_coef=vf_coef,
                max_grad_norm=max_grad_norm,
                optim=OptimizerFactoryFactoryRMSprop(eps=1e-5, alpha=0.99),
                lr=lr,
                lr_scheduler=LRSchedulerFactoryFactoryLinear(training_config) if lr_decay else None,
            ),
        )
        .with_actor_factory_default(hidden_sizes, nn.Tanh, continuous_unbounded=True)
        .with_critic_factory_default(hidden_sizes, nn.Tanh)
        .build()
    )
    experiment.run(run_name=log_name)


if __name__ == "__main__":
    logging.run_cli(main)
