#!/usr/bin/env python3
import argparse

# idmtools ...
from idmtools.builders import SimulationBuilder
from idmtools.core.platform_factory import Platform
from idmtools.entities.experiment import Experiment

# emodpy
from emodpy.emod_task import EMODTask

from simulations.helpers import *
import simulations.params as params
from simulations import manifest as manifest


def general_sim(site=None, nSims=2):
    """
    This function is designed to be a parameterized version of the sequence of things we do 
    every time we run an emod experiment. 
    """

    # Create a platform
    # Show how to dynamically set priority and node_group
    platform = Platform("Calculon", priority='normal')  # , node_group='idm_48cores')

    # create EMODTask 
    print("Creating EMODTask (from files)...")
    
    task = EMODTask.from_default2(
            config_path="my_config.json",
            eradication_path=str(manifest.eradication_path),
            ep4_custom_cb=None,
            campaign_builder=None,
            schema_path=str(manifest.schema_file),
            param_custom_cb=set_param_fn,
            demog_builder=None,
        )

    # Create simulation sweep with builder
    builder = SimulationBuilder()


    exp_name = "validation_" + site

    # Sweep run number
    builder.add_sweep_definition(update_sim_random_seed, range(nSims))

    # Sweep sites and seeds - based on values in simulation_coordinator csv
    # builder.add_sweep_definition(set_simulation_scenario, [site])
    # set_simulation_scenario_for_matched_site = partial(set_simulation_scenario, csv_path=manifest.simulation_coordinator_path)
    #set_simulation_scenario_for_sweep_site = partial(set_simulation_scenario, csv_path=manifest.simulation_coordinator_path)
    builder.add_sweep_definition(partial(set_simulation_scenario, csv_path=manifest.simulation_coordinator_path), [site])

    # create experiment from builder
    print( f"Prompting for COMPS creds if necessary..." )
    experiment = Experiment.from_builder(builder, task, name=exp_name)

    # The last step is to call run() on the ExperimentManager to run the simulations.
    experiment.run(wait_until_done=False, platform=platform)

    # Save experiment id to file
    with open(f"{site}_COMPS_ID_submit", "w") as fd:
        fd.write(experiment.uid.hex)
    print()
    print(experiment.uid.hex)
    return experiment.uid.hex


if __name__ == "__main__":
    # TBD: user should be allowed to specify (override default) erad_path and input_path from command line 
    # plan = EradicationBambooBuilds.MALARIA_LINUX
    # print("Retrieving Eradication and schema.json from Bamboo...")
    # get_model_files( plan, manifest )
    # print("...done.")
    
    parser = argparse.ArgumentParser(description='Process site name')
    parser.add_argument('--site', '-s', type=str, help='site name', default='sugungum_1970')#params.sites[0]) # not sure if we want to make this required argument
    parser.add_argument('--nSims', '-n', type=int, help='number of simulations', default=2)#params.nSims)
    args = parser.parse_args()

    general_sim(site=args.site, nSims=args.nSims)
