
#### Malaria_model_validation_output_10-15-2024(12-34-38).pdf
This file is the team defaults as of 10/15/24.

#### Malaria_model_validation_output_10-16-2024(09-36-21).pdf
This file changes Max_Individual_Infections to 21, and increases the other antigen space parameters linearly (by a factor of 7)
```     
increase_factor = 7
config.parameters.Max_Individual_Infections = 3*increase_factor
config.parameters.Falciparum_MSP_Variants = 32*increase_factor
config.parameters.Falciparum_Nonspecific_Types = 76*increase_factor
config.parameters.Falciparum_PfEMP1_Variants = 1070*increase_factor
```
- Takeaway: this increased the incidence for all ages, and made older ages a lot more prone to infection/infectiousness

#### Malaria_model_validation_output_10-16-2024(11-05-38).pdf
This file changes Max_Individual_Infections to 21, and increases the other antigen space parameters geometrically (by a factor of sqrt(7) ~ 2.6)
```     
    increase_factor = np.sqrt(7)
    config.parameters.Max_Individual_Infections = round(3*increase_factor)
    config.parameters.Falciparum_MSP_Variants = round(32*increase_factor)
    config.parameters.Falciparum_Nonspecific_Types = round(76*increase_factor)
    config.parameters.Falciparum_PfEMP1_Variants = round(1070*increase_factor)
```
- Takeaway: this wasn't quite as extreme as the linear increase, but still increased the incidence for all ages, and made older ages a lot more prone to infection/infectiousness

NOTE: I was mistakenly reducing Max_Individual_Infections when I meant to keep it constant.

#### Malaria_model_validation_output_10-16-2024(12-54-40).pdf
This file changes Max_Individual_Infections to 21, and increases the other antigen space parameters geometrically (by a factor of 7**(1/3) ~ 1.9)
```     
    increase_factor = 7**(1/3)
    config.parameters.Max_Individual_Infections = round(3*increase_factor)
    config.parameters.Falciparum_MSP_Variants = round(32*increase_factor)
    config.parameters.Falciparum_Nonspecific_Types = round(76*increase_factor)
    config.parameters.Falciparum_PfEMP1_Variants = round(1070*increase_factor)
```
- Takeaway: this wasn't quite as extreme as the linear increase, but still increased the incidence for all ages, and made older ages a lot more prone to infection/infectiousness
NOTE: I was mistakenly reducing Max_Individual_Infections when I meant to keep it constant.

#### Malaria_model_validation_output_10-16-2024(15-07-21).pdf
Correctly changes Max_Individual_Infections to 21, and increases the other antigen space parameters geometrically (by a factor of 7**(1/2) ~ 2.6)

#### Malaria_model_validation_output_11-19-2024(16-26-02).pdf
Tobias' most recent "good-fit" for 20 max infections.

parameter,param_set,emod_value,team_default
Antigen_Switch_Rate,31,5.142077320821176e-09,7.65e-10
Base_Gametocyte_Fraction_Male,31,0.2043390314448797,0.2
Base_Gametocyte_Mosquito_Survival_Rate,31,0.000961769,0.00088
Base_Gametocyte_Production_Rate,31,0.3270759557024592,0.0615
Falciparum_MSP_Variants,31,1,32
Falciparum_Nonspecific_Types,31,102,76
Falciparum_PfEMP1_Variants,31,2633,1070
Fever_IRBC_Kill_Rate,31,867.8046693042583,1.4
Gametocyte_Stage_Survival_Rate,31,0.8375622366632939,0.5886
MSP1_Merozoite_Kill_Fraction,31,0.47869092622274845,0.511735322
Nonspecific_Antibody_Growth_Rate_Factor,31,110.92328271035161,0.5
Nonspecific_Antigenicity_Factor,31,0.088390561,0.4151
Pyrogenic_Threshold,31,3531.9755568364235,15000
Cytokine_Gametocyte_Inactivation,31,0.005139703,0.02

### Next
Run with Max_Individual_Infections set to 100, and nothing else modified