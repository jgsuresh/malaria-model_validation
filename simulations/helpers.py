import os
import warnings
import pandas as pd
import numpy as np
from functools import partial
import emod_api.demographics.Demographics as Demographics

from emodpy_malaria.interventions.diag_survey import add_diagnostic_survey

from emodpy_malaria.reporters.builtin import add_malaria_summary_report, MalariaPatientJSONReport
from emodpy_malaria import malaria_config as malconf
from emodpy_malaria.interventions.drug_campaign import add_drug_campaign
from emodpy_malaria.interventions.treatment_seeking import add_treatment_seeking
from emodpy_malaria.interventions.inputeir import add_scheduled_input_eir
from emod_api.interventions.common import BroadcastEvent
import simulations.manifest as manifest


def update_sim_random_seed(simulation, value):
    simulation.task.config.parameters.Run_Number = value
    return {"Run_Number": value}


def mAb_vs_EIR(EIR):
    # Rough cut at function from eyeballing a few BinnedReport outputs parsed into antibody fractions
    mAb = 0.9 * (1e-4*EIR*EIR + 0.7*EIR) / ( 0.7*EIR + 2 )
    return min(mAb, 1.0)


def update_mab(simulation, value):
    simulation.task.config.parameters.Maternal_Antibody_Protection *= value
    return None


def set_param_fn(config):
    """
    This function is a callback that is passed to emod-api.config to set parameters The Right Way.
    """
    config = malconf.set_team_defaults(config, manifest)
    # config = set_config.set_config(config)

    config.parameters.Base_Rainfall = 150
    config.parameters.Climate_Model = "CLIMATE_CONSTANT"
    config.parameters.Enable_Disease_Mortality = 0
    config.parameters.Enable_Vector_Species_Report = 0
    config.parameters.Enable_Vital_Dynamics = 0
    config.parameters.Simulation_Duration = 70*365
    config.parameters.Enable_Initial_Prevalence = 1
    config.parameters.Vector_Species_Params = []
    config.parameters.Start_Time = 0
    # update microscopy parameters
    config.parameters.Report_Detection_Threshold_Blood_Smear_Gametocytes = 0  # 20
    config.parameters.Report_Detection_Threshold_Blood_Smear_Parasites = 0  # 20
    config.parameters.Report_Gametocyte_Smear_Sensitivity = 0.01  # 0.1
    config.parameters.Report_Parasite_Smear_Sensitivity = 0.01  # 0.1

    # Try running with expanded antigen space
    max_individual_infections_increase_factor = 7
    other_antigen_increase_factor = max_individual_infections_increase_factor**0.5
    config.parameters.Max_Individual_Infections = 3 * max_individual_infections_increase_factor
    config.parameters.Falciparum_MSP_Variants = round(32*other_antigen_increase_factor)
    config.parameters.Falciparum_Nonspecific_Types = round(76*other_antigen_increase_factor)
    config.parameters.Falciparum_PfEMP1_Variants = round(1070*other_antigen_increase_factor)



    # config.parameters.Clinical_Fever_Threshold_High = 0.1
    # config.parameters.Clinical_Fever_Threshold_Low = 0.1
    # config.parameters.pop("Serialized_Population_Filenames")

    return config


# def update_camp_type(simulation, site):
#     # simulation.task.config.parameters.Run_Number = value
#     build_camp_partial = partial(build_camp, site=site)
#     simulation.task.create_campaign_from_callback(build_camp_partial)
#
#     update_mab(simulation, mAb_vs_EIR(sum(study_site_monthly_EIRs[site])))
#
#     return {"Site": site}


def set_simulation_scenario(simulation, site, csv_path):
    # get information on this simulation setup from coordinator csv
    coord_df = pd.read_csv(csv_path)
    coord_df = coord_df.set_index('site')

    # === set up config === #
    # simulation duration
    simulation_duration = int(coord_df.at[site, 'simulation_duration'])
    simulation.task.config.parameters.Simulation_Duration = simulation_duration
    # add demographics and set whether there are births and deaths
    demographics_filename = str(coord_df.at[site, 'demographics_filepath'])
    if demographics_filename and demographics_filename != 'nan':
        simulation.task.transient_assets.add_asset(manifest.input_files_path / demographics_filename)
        simulation.task.config.parameters.Demographics_Filenames = [demographics_filename.rsplit('/',1)[-1]]
    simulation.task.config.parameters.Enable_Vital_Dynamics = coord_df.at[site, 'enable_vital_dynamics'].tolist()
    if coord_df.at[site, 'enable_vital_dynamics'] == 1:
        simulation.task.config.parameters.Age_Initialization_Distribution_Type = 'DISTRIBUTION_COMPLEX'
    else:
        simulation.task.config.parameters.Age_Initialization_Distribution_Type = 'DISTRIBUTION_SIMPLE'
    # maternal antibodies - use first 12 months of data frame to get annual EIR from monthly eir
    monthly_eirs = pd.read_csv(manifest.input_files_path / coord_df.at[site, 'EIR_filepath'])
    update_mab(simulation, mAb_vs_EIR(sum(monthly_eirs.loc[monthly_eirs.index[0:12], site])))

    # === set up campaigns === #
    build_camp_partial = partial(build_camp, site=site, coord_df=coord_df)
    simulation.task.create_campaign_from_callback(build_camp_partial)

    # === set up reporters === #
    report_start_day = int(coord_df.at[site, 'report_start_day'])
    if (not pd.isna(coord_df.at[site, 'par_dens_bins'])) and (not (coord_df.at[site, 'par_dens_bins'] == '')):
        density_bins_df = pd.read_csv(manifest.input_files_path / 'report_density_bins' / 'density_bin_sets.csv')
        density_bins_df = density_bins_df[coord_df.at[site, 'par_dens_bins']].tolist()
        density_bins_df = [x for x in density_bins_df if pd.notnull(x)]
    else:
        density_bins_df = [0, 50, 500, 5000, 5000000]
    if coord_df.at[site, 'include_AnnualMalariaSummaryReport']:
        if (not pd.isna(coord_df.at[site, 'annual_summary_report_age_bins'])) and (not (coord_df.at[site, 'annual_summary_report_age_bins'] == '')):
            summary_report_age_bins_df = pd.read_csv(manifest.input_files_path / 'summary_report_age_bins' / 'age_bin_sets.csv')
            summary_report_age_bins = summary_report_age_bins_df[coord_df.at[site, 'annual_summary_report_age_bins']].tolist()
            summary_report_age_bins = [x for x in summary_report_age_bins if pd.notnull(x)]
        else:
            summary_report_age_bins = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 14, 19, 39, 59, 85]

        add_malaria_summary_report(simulation.task, manifest=manifest, start_day=report_start_day,
                                   end_day=1000000 + report_start_day,
                                   reporting_interval=365, age_bins=summary_report_age_bins,
                                   infectiousness_bins=[0, 100], max_number_reports=2000,
                                   parasitemia_bins=density_bins_df, filename_suffix='Annual_Report')

    if coord_df.at[site, 'include_MonthlyMalariaSummaryReport']:
        if (not pd.isna(coord_df.at[site, 'monthly_summary_report_age_bins'])) and (not (coord_df.at[site, 'monthly_summary_report_age_bins'] == '')):
            summary_report_age_bins_df = pd.read_csv(manifest.input_files_path / 'summary_report_age_bins' / 'age_bin_sets.csv')
            summary_report_age_bins = summary_report_age_bins_df[coord_df.at[site, 'monthly_summary_report_age_bins']].tolist()
            summary_report_age_bins = [x for x in summary_report_age_bins if pd.notnull(x)]
        else:
            summary_report_age_bins = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 14, 19, 39, 59, 85]

        for yy in range(report_start_day, simulation_duration, 365):
            add_malaria_summary_report(simulation.task, manifest=manifest, start_day=yy, end_day=365 + yy,
                                       reporting_interval=30, age_bins=summary_report_age_bins,
                                       infectiousness_bins=[0, 100], max_number_reports=1000,
                                       parasitemia_bins=density_bins_df,
                                       filename_suffix='Monthly_Report_%i' % int(round(yy/365)))

        if coord_df.at[site, 'infectiousness_to_mosquitos']:
            for yy in range(report_start_day, simulation_duration, 365):
                add_malaria_summary_report(simulation.task, manifest=manifest, start_day=yy, end_day=365 + yy,
                                           reporting_interval=30, age_bins=summary_report_age_bins,
                                           infectiousness_bins=[0, 5, 20, 50, 80, 100], max_number_reports=1000,
                                           parasitemia_bins=density_bins_df,
                                           filename_suffix='Infectiousness_Monthly_Report_%i' % int(round(yy / 365)))

    if coord_df.at[site, 'include_MalariaPatientReport']:
        patient_report = MalariaPatientJSONReport()  # Create the reporter
        patient_report.config(ptr_config_builder, manifest)  # Config the reporter
        simulation.task.reporters.add_reporter(patient_report)  # Add the reporter

    if coord_df.at[site, 'include_parDensSurveys']:  # surveys added as a campaign in build_camp()
        simulation.task.config.parameters.Report_Event_Recorder = 1
        simulation.task.config.parameters.Report_Event_Recorder_Events = ['parasites_on_survey_day']
        simulation.task.config.parameters.Custom_Individual_Events = ['parasites_on_survey_day']

    return {"Site": site, 'csv_path': str(csv_path)}


set_simulation_scenario_for_matched_site = partial(set_simulation_scenario, csv_path=manifest.simulation_coordinator_path)
set_simulation_scenario_for_characteristic_site = partial(set_simulation_scenario, csv_path=manifest.sweep_sim_coordinator_path)


def build_standard_campaign_object(manifest):
    import emod_api.campaign as campaign
    campaign.set_schema(manifest.schema_file)
    return campaign


# def build_camp(site, cross_sectional_surveys=False, survey_days=None):
def build_camp(site, coord_df):
    """
    Build a campaign input file for the DTK using emod_api.
    Right now this function creates the file and returns the filename. If calling code just needs an asset that's fine.
    """
    # create campaign object
    camp = build_standard_campaign_object(manifest)

    # === EIR === #

    # set monthly eir for site - TODO - change to daily EIR
    monthly_eirs = pd.read_csv(manifest.input_files_path / coord_df.at[site, 'EIR_filepath'])
    # TODO - currently recycles first 12 values; should update to use multiple years if provided
    add_scheduled_input_eir(camp, monthly_eir=monthly_eirs.loc[monthly_eirs.index[0:12], site].tolist(),
                            start_day=0, age_dependence="SURFACE_AREA_DEPENDENT")

    # === INTERVENTIONS === #

    # health-seeking
    if (not pd.isna(coord_df.at[site, 'CM_filepath'])) and (not (coord_df.at[site, 'CM_filepath'] == '')):
        hs_df = pd.read_csv(manifest.input_files_path / coord_df.at[site, 'CM_filepath'])
    else:
        hs_df = pd.DataFrame()
    # NMFs
    if (not pd.isna(coord_df.at[site, 'NMF_filepath'])) and (not (coord_df.at[site, 'NMF_filepath'] == '')):
        nmf_df = pd.read_csv(manifest.input_files_path / coord_df.at[site, 'NMF_filepath'])
    else:
        nmf_df = pd.DataFrame()

    if not hs_df.empty:
        # case management for malaria
        add_hfca_hs(camp, hs_df)
        # case management for NMFs
        add_nmf_hs(camp, hs_df, nmf_df)


    # === SURVEYS === #

    # add parasite density surveys among individuals with parasitemia
    if coord_df.at[site, 'include_parDensSurveys'] and (not pd.isna(coord_df.at[site, 'include_parDensSurveys'])):
        # adding schema file, so it can be looked up when creating the campaigns
        camp.schema_path = manifest.schema_file
        survey_days = pd.read_csv(manifest.input_files_path / coord_df.at[site, 'survey_days_filepath']).loc['days']
        add_broadcasting_survey(camp, survey_days=survey_days)

    return camp


def add_hfca_hs(camp, hs_df):
    for r, row in hs_df.iterrows() :
        add_hs_from_file(camp, row)


def add_hs_from_file(camp, row):
    hs_child = row['U5_coverage']
    hs_adult = row['adult_coverage']
    severe_cases = row['severe_coverage']
    start_day = row['simday']
    duration = row['duration']
    if 'drug_code' in row.index:
        drug_code = row['drug_code']
    else:
        drug_code = 'AL'
    if drug_code == 'AL':
        drug = ['Artemether', 'Lumefantrine']
    elif drug_code == 'SP':
        drug = ['Sulfadoxine', 'Pyrimethamine']
    elif drug_code == 'CQ':
        drug = ['Chloroquine']
    else:
        warnings.warn('Drug code not recognized. Assuming AL.')
        drug = ['Artemether', 'Lumefantrine']

    add_treatment_seeking(camp, start_day=start_day,
                          targets=[{'trigger': 'NewClinicalCase', 'coverage': hs_child, 'agemin': 0, 'agemax': 5,
                                   'seek': 1, 'rate': 0.3},
                                   {'trigger': 'NewClinicalCase', 'coverage': hs_adult, 'agemin': 5, 'agemax': 100,
                                    'seek': 1, 'rate': 0.3}],
                          drug=drug, duration=duration)
    add_treatment_seeking(camp, start_day=start_day,
                          targets=[{'trigger': 'NewSevereCase', 'coverage': severe_cases, 'seek': 1, 'rate': 0.5}], #change by adding column and reviewing literature
                          drug=drug, duration=duration)  # , broadcast_event_name='Received_Severe_Treatment')


def add_nmf_hs(camp, hs_df, nmf_df):
    # if no NMF rate is specified, assume all age groups have 0.0038 probability each day
    if nmf_df.empty:
        nmf_df = pd.DataFrame({'U5_nmf': [0.0038], 'adult_nmf': [0.0038]})
    elif nmf_df.shape[0] != 1:
        warnings.warn('The NMF dataframe has more than one row. Only values in the first row will be used.')
    nmf_row = nmf_df.iloc[0]

    # apply the health-seeking rate for clinical malaria to NMFs
    for r, row in hs_df.iterrows():
        add_nmf_hs_from_file(camp, row, nmf_row)


def add_nmf_hs_from_file(camp, row, nmf_row):
    hs_child = row['U5_coverage']
    hs_adult = row['adult_coverage']
    start_day = row['simday']
    duration = row['duration']
    if 'drug_code' in row.index:
        drug_code = row['drug_code']
    else:
        drug_code = 'AL'
    if start_day == 0:  # due to dtk diagnosis/treatment configuration, a start day of 0 is not supported
        start_day = 1  # start looking for NMFs on day 1 (not day 0) of simulation
        if duration > 1:
            duration = duration - 1
    nmf_child = nmf_row['U5_nmf']
    nmf_adult = nmf_row['adult_nmf']

    # workaround for maximum duration of 1000 days is to loop, creating a new campaign every 1000 days
    separate_durations = [1000] * int(np.floor(duration/1000))  # create a separate campaign for each 1000 day period
    if (duration - np.floor(duration/1000) > 0):  # add final remaining non-1000-day duration
        separate_durations = separate_durations + [int(duration - np.floor(duration/1000) * 1000)]
    separate_start_days = start_day + np.array([0] + list(np.cumsum(separate_durations)))
    for dd in range(len(separate_durations)):
        if nmf_child * hs_child > 0:
            add_drug_campaign(camp, 'MSAT', drug_code=drug_code, start_days=[separate_start_days[dd]],
                              target_group={'agemin': 0, 'agemax': 5},
                              coverage=nmf_child * hs_child,
                              repetitions=separate_durations[dd], tsteps_btwn_repetitions=1,
                              diagnostic_type='PF_HRP2', diagnostic_threshold=5,
                              receiving_drugs_event_name='Received_NMF_Treatment')
        if nmf_adult * hs_adult > 0:
            add_drug_campaign(camp, 'MSAT', drug_code=drug_code, start_days=[separate_start_days[dd]],
                              target_group={'agemin': 5, 'agemax': 120},
                              coverage=nmf_adult * hs_adult,
                              repetitions=separate_durations[dd], tsteps_btwn_repetitions=1,
                              diagnostic_type='PF_HRP2', diagnostic_threshold=5,
                              receiving_drugs_event_name='Received_NMF_Treatment')


def ptr_config_builder(params):
    return params


def add_broadcasting_survey(camp, survey_days, include_neg_broadcast=False):
    pos_diag_cfg = BroadcastEvent(camp=camp, Event_Trigger='parasites_on_survey_day')
    neg_diag_cfg = BroadcastEvent(camp=camp, Event_Trigger='negative_test_on_survey_day')
    for survey_day in survey_days:
        if include_neg_broadcast:
            add_diagnostic_survey(camp=camp, start_day=survey_day,
                                  diagnostic_type='TRUE_PARASITE_DENSITY', diagnostic_threshold=0,
                                  positive_diagnosis_configs=[pos_diag_cfg], negative_diagnosis_configs=[neg_diag_cfg])
        else:
            add_diagnostic_survey(camp=camp, start_day=survey_day,
                                  diagnostic_type='TRUE_PARASITE_DENSITY', diagnostic_threshold=0,
                                  positive_diagnosis_configs=[pos_diag_cfg])


def build_demog():
    """
    Build a demographics input file for the DTK using emod_api.
    Right now this function creates the file and returns the filename. If calling code just needs an asset that's fine.
    Also right now this function takes care of the config updates that are required as a result of specific demog settings. We do NOT want the emodpy-disease developers to have to know that. It needs to be done automatically in emod-api as much as possible.
    TBD: Pass the config (or a 'pointer' thereto) to the demog functions or to the demog class/module.

    """
    demog = Demographics.from_file(manifest)

    return demog


def get_comps_id_filename(site: str, level: int = 0):
    folder_name = manifest.comps_id_folder
    if level == 0:
        file_name = folder_name / (site + '_exp_submit')
    elif level == 1:
        file_name = folder_name / (site + '_exp_done')
    elif level == 2:
        file_name = folder_name / (site + '_analyzers')
    else:
        file_name = folder_name / (site + '_download')
    return file_name.relative_to(manifest.CURRENT_DIR).as_posix()


def load_coordinator_df(characteristic=False, set_index=True):
    csv_file = manifest.sweep_sim_coordinator_path if characteristic else manifest.simulation_coordinator_path
    coord_df = pd.read_csv(csv_file)
    if set_index:
        coord_df = coord_df.set_index('site')
    return coord_df


def get_suite_id():
    if os.path.exists(manifest.suite_id_file):
        with open(manifest.suite_id_file, 'r') as id_file:
            suite_id = id_file.readline()
        return suite_id
    else:
        return 0


