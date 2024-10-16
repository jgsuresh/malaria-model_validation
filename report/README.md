
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