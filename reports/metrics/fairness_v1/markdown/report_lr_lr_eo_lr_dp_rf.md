# Fairness × Accuracy Report

_Models:_ **lr, lr_eo, lr_dp, rf**  

_Significance (Holm-adj):_ α = **0.05**  


---

## Accuracy Summary

| model | macro_f1@0.5 | micro_f1@0.5 | macro_auroc | macro_auprc | brier | ece |
|---|---|---|---|---|---|---|
| lr | 0.978 | 0.982 | 0.994 | 0.990 | 0.007 | 0.005 |
| lr_eo | 0.971 | 0.974 | 0.980 | 0.971 | 0.011 | 0.011 |
| lr_dp | 0.719 | 0.838 | 0.823 | 0.731 | 0.060 | 0.060 |
| rf | 0.869 | 0.890 | 0.970 | 0.937 | 0.041 | 0.054 |


---

## Fairness Summary (Subgroups)

### Model: `lr`

**Number of significant subgroup gaps by metric (Holm-adj):**


| namespace | metric | n_significant |
|---|---|---|
| age | DP | 18 |
| age | EO | 14 |
| age | FPR | 6 |
| dp_age | DP | 12 |
| dp_age | EO | 16 |
| dp_age | FPR | 2 |
| dp_gender | DP | 8 |
| dp_gender | EO | 2 |
| dp_gender | FPR | 0 |
| dp_hair_color | DP | 12 |
| dp_hair_color | EO | 10 |
| dp_hair_color | FPR | 1 |
| dp_nationality | DP | 31 |
| dp_nationality | EO | 9 |
| dp_nationality | FPR | 0 |
| dp_race_ethnicity | DP | 38 |
| dp_race_ethnicity | EO | 22 |
| dp_race_ethnicity | FPR | 8 |
| dp_sexuality | DP | 0 |
| dp_sexuality | EO | 0 |
| dp_sexuality | FPR | 0 |
| eo_age | DP | 20 |
| eo_age | EO | 10 |
| eo_age | FPR | 4 |
| eo_gender | DP | 16 |
| eo_gender | EO | 2 |
| eo_gender | FPR | 4 |
| eo_hair_color | DP | 20 |
| eo_hair_color | EO | 7 |
| eo_hair_color | FPR | 2 |
| eo_nationality | DP | 39 |
| eo_nationality | EO | 7 |
| eo_nationality | FPR | 2 |
| eo_race_ethnicity | DP | 47 |
| eo_race_ethnicity | EO | 15 |
| eo_race_ethnicity | FPR | 12 |
| eo_sexuality | DP | 0 |
| eo_sexuality | EO | 0 |
| eo_sexuality | FPR | 0 |
| gender | DP | 16 |
| gender | EO | 4 |
| gender | FPR | 4 |
| hair_color | DP | 21 |
| hair_color | EO | 12 |
| hair_color | FPR | 2 |
| nationality | DP | 39 |
| nationality | EO | 4 |
| nationality | FPR | 5 |
| race_ethnicity | DP | 45 |
| race_ethnicity | EO | 14 |
| race_ethnicity | FPR | 15 |
| sexuality | DP | 0 |
| sexuality | EO | 0 |
| sexuality | FPR | 0 |


#### age

**Top 10 by Δ Demographic Parity:**


| class | subgroup | dp_diff | n_sub | p_dp_adj |
|---|---|---|---|---|
| Big Tits | age_young | -0.274 | 1507.000 | 0.000 |
| Teens | age_young | 0.262 | 1507.000 | 0.000 |
| Big Tits | age_mature | 0.140 | 2954.000 | 0.000 |
| Teens | age_mature | -0.134 | 2954.000 | 0.000 |
| Blonde | age_young | -0.107 | 1507.000 | 0.000 |
| Amateur | age_young | 0.074 | 1507.000 | 0.000 |
| Blonde | age_mature | 0.055 | 2954.000 | 0.000 |
| Lesbian | age_young | -0.038 | 1507.000 | 0.000 |
| Amateur | age_mature | -0.038 | 2954.000 | 0.000 |
| Group | age_young | -0.037 | 1507.000 | 0.000 |

**Top 10 by Δ Equal Opportunity:**


| class | subgroup | eo_diff | n_sub | p_eo_adj |
|---|---|---|---|---|
| Cumshot | age_young | -0.060 | 1507.000 | 0.000 |
| Cumshot | age_mature | 0.038 | 2954.000 | 0.000 |
| Asian | age_young | 0.023 | 1507.000 | 0.136 |
| Group | age_young | 0.021 | 1507.000 | 0.338 |
| Fetish | age_young | -0.019 | 1507.000 | 0.248 |
| Blonde | age_young | -0.019 | 1507.000 | 0.002 |
| Masturbation | age_young | -0.017 | 1507.000 | 0.036 |
| Blowjob | age_young | -0.017 | 1507.000 | 0.003 |
| Asian | age_mature | -0.015 | 2954.000 | 0.136 |
| Big Tits | age_young | -0.014 | 1507.000 | 0.002 |

**Top 10 by Δ False Positive Rate:**


| class | subgroup | fpr_diff | n_sub | p_fpr_adj |
|---|---|---|---|---|
| Amateur | age_young | 0.016 | 1507.000 | 0.000 |
| Amateur | age_mature | -0.007 | 2954.000 | 0.000 |
| Masturbation | age_young | 0.006 | 1507.000 | 0.043 |
| Big Tits | age_mature | 0.005 | 2954.000 | 0.197 |
| Big Tits | age_young | -0.005 | 1507.000 | 0.197 |
| Teens | age_young | 0.004 | 1507.000 | 0.004 |
| Fetish | age_young | 0.003 | 1507.000 | 0.250 |
| Masturbation | age_mature | -0.003 | 2954.000 | 0.043 |
| Fetish | age_mature | -0.002 | 2954.000 | 0.250 |
| Blonde | age_young | 0.002 | 1507.000 | 0.903 |


#### dp_age

**Top 10 by Δ Demographic Parity:**


| class | subgroup | dp_diff | n_sub | p_dp_adj |
|---|---|---|---|---|
| Big Tits | age_young | -0.220 | 1507.000 | 0.000 |
| Big Tits | age_mature | 0.112 | 2954.000 | 0.000 |
| Teens | age_young | 0.112 | 1507.000 | 0.000 |
| Blonde | age_young | -0.099 | 1507.000 | 0.000 |
| Teens | age_mature | -0.057 | 2954.000 | 0.000 |
| Blonde | age_mature | 0.051 | 2954.000 | 0.000 |
| Blowjob | age_young | -0.042 | 1507.000 | 0.000 |
| Masturbation | age_young | -0.036 | 1507.000 | 0.000 |
| Group | age_young | -0.033 | 1507.000 | 0.000 |
| Blowjob | age_mature | 0.021 | 2954.000 | 0.000 |

**Top 10 by Δ Equal Opportunity:**


| class | subgroup | eo_diff | n_sub | p_eo_adj |
|---|---|---|---|---|
| Teens | age_mature | 0.218 | 2954.000 | 0.000 |
| Group | age_young | -0.132 | 1507.000 | 0.014 |
| Blonde | age_young | -0.126 | 1507.000 | 0.000 |
| Cumshot | age_young | -0.114 | 1507.000 | 0.000 |
| Amateur | age_young | -0.113 | 1507.000 | 0.000 |
| Amateur | age_mature | 0.080 | 2954.000 | 0.000 |
| Teens | age_young | -0.074 | 1507.000 | 0.000 |
| Cumshot | age_mature | 0.074 | 2954.000 | 0.000 |
| Big Tits | age_young | -0.068 | 1507.000 | 0.002 |
| Lesbian | age_young | 0.043 | 1507.000 | 0.091 |

**Top 10 by Δ False Positive Rate:**


| class | subgroup | fpr_diff | n_sub | p_fpr_adj |
|---|---|---|---|---|
| Masturbation | age_young | 0.004 | 1507.000 | 0.047 |
| Big Tits | age_mature | -0.003 | 2954.000 | 0.113 |
| Big Tits | age_young | 0.003 | 1507.000 | 0.113 |
| Amateur | age_young | 0.003 | 1507.000 | 0.714 |
| Fetish | age_young | 0.002 | 1507.000 | 0.295 |
| Masturbation | age_mature | -0.002 | 2954.000 | 0.047 |
| Fetish | age_mature | -0.001 | 2954.000 | 0.295 |
| Amateur | age_mature | -0.001 | 2954.000 | 0.714 |
| Anal | age_young | 0.001 | 1507.000 | 0.432 |
| Blowjob | age_young | -0.001 | 1507.000 | 0.580 |


#### dp_gender

**Top 10 by Δ Demographic Parity:**


| class | subgroup | dp_diff | n_sub | p_dp_adj |
|---|---|---|---|---|
| Blowjob | gender_male | 0.321 | 185.000 | 0.000 |
| Masturbation | gender_male | -0.204 | 185.000 | 0.000 |
| Cumshot | gender_male | 0.057 | 185.000 | 0.000 |
| Group | gender_male | 0.048 | 185.000 | 0.000 |
| Teens | gender_male | 0.045 | 185.000 | 0.076 |
| Blonde | gender_male | 0.030 | 185.000 | 0.481 |
| Blowjob | gender_female | -0.026 | 2274.000 | 0.000 |
| Amateur | gender_male | -0.026 | 185.000 | 0.769 |
| Big Tits | gender_male | -0.026 | 185.000 | 0.821 |
| Masturbation | gender_female | 0.017 | 2274.000 | 0.000 |

**Top 10 by Δ Equal Opportunity:**


| class | subgroup | eo_diff | n_sub | p_eo_adj |
|---|---|---|---|---|
| Cumshot | gender_male | -0.177 | 185.000 | 0.023 |
| Anal | gender_male | 0.118 | 185.000 | 0.612 |
| Masturbation | gender_male | 0.099 | 185.000 | 0.186 |
| Fetish | gender_male | 0.093 | 185.000 | 0.706 |
| Cumshot | gender_female | 0.055 | 2274.000 | 0.023 |
| Interracial | gender_male | -0.051 | 185.000 | 0.633 |
| Big Tits | gender_male | -0.045 | 185.000 | 0.762 |
| Amateur | gender_male | 0.042 | 185.000 | 0.930 |
| Blowjob | gender_male | 0.040 | 185.000 | 0.577 |
| Asian | gender_male | 0.035 | 185.000 | 0.798 |

**Top 10 by Δ False Positive Rate:**


| class | subgroup | fpr_diff | n_sub | p_fpr_adj |
|---|---|---|---|---|
| Cumshot | gender_male | 0.005 | 185.000 | 0.125 |
| Big Tits | gender_male | -0.005 | 185.000 | 0.830 |
| Fetish | gender_male | 0.002 | 185.000 | 1.000 |
| Anal | gender_male | -0.002 | 185.000 | 1.000 |
| Teens | gender_male | -0.001 | 185.000 | 1.000 |
| Amateur | gender_male | -0.001 | 185.000 | 1.000 |
| Asian | gender_male | -0.000 | 185.000 | 1.000 |
| Big Tits | gender_female | 0.000 | 2274.000 | 0.830 |
| Cumshot | gender_female | -0.000 | 2274.000 | 0.125 |
| Anal | gender_female | -0.000 | 2274.000 | 1.000 |


#### dp_hair_color

**Top 10 by Δ Demographic Parity:**


| class | subgroup | dp_diff | n_sub | p_dp_adj |
|---|---|---|---|---|
| Blonde | blonde | 0.345 | 3954.000 | 0.000 |
| Blonde | brunette | -0.200 | 6045.000 | 0.000 |
| Blonde | redhead | -0.188 | 821.000 | 0.000 |
| Blowjob | redhead | -0.113 | 821.000 | 0.000 |
| Amateur | redhead | 0.052 | 821.000 | 0.000 |
| Big Tits | blonde | 0.046 | 3954.000 | 0.000 |
| Teens | redhead | -0.031 | 821.000 | 0.052 |
| Big Tits | brunette | -0.031 | 6045.000 | 0.000 |
| Masturbation | redhead | -0.025 | 821.000 | 0.226 |
| Blowjob | blonde | 0.016 | 3954.000 | 0.021 |

**Top 10 by Δ Equal Opportunity:**


| class | subgroup | eo_diff | n_sub | p_eo_adj |
|---|---|---|---|---|
| Blonde | brunette | -0.248 | 6045.000 | 0.000 |
| Blonde | redhead | -0.214 | 821.000 | 0.000 |
| Masturbation | redhead | -0.119 | 821.000 | 0.000 |
| Big Tits | redhead | -0.111 | 821.000 | 0.000 |
| Blowjob | redhead | -0.101 | 821.000 | 0.000 |
| Anal | redhead | -0.078 | 821.000 | 0.055 |
| Asian | redhead | 0.068 | 821.000 | 0.669 |
| Group | redhead | -0.062 | 821.000 | 0.440 |
| Blonde | blonde | 0.057 | 3954.000 | 0.000 |
| Teens | redhead | -0.046 | 821.000 | 0.179 |

**Top 10 by Δ False Positive Rate:**


| class | subgroup | fpr_diff | n_sub | p_fpr_adj |
|---|---|---|---|---|
| Amateur | redhead | 0.004 | 821.000 | 0.466 |
| Blowjob | redhead | 0.002 | 821.000 | 0.004 |
| Teens | redhead | 0.002 | 821.000 | 0.061 |
| Big Tits | blonde | -0.001 | 3954.000 | 0.840 |
| Amateur | blonde | -0.001 | 3954.000 | 1.000 |
| Masturbation | redhead | -0.001 | 821.000 | 1.000 |
| Anal | redhead | -0.001 | 821.000 | 0.629 |
| Fetish | blonde | -0.001 | 3954.000 | 0.918 |
| Big Tits | brunette | 0.001 | 6045.000 | 0.840 |
| Big Tits | redhead | -0.000 | 821.000 | 0.855 |


#### dp_nationality

**Top 10 by Δ Demographic Parity:**


| class | subgroup | dp_diff | n_sub | p_dp_adj |
|---|---|---|---|---|
| Blowjob | south_asian | -0.313 | 128.000 | 0.000 |
| Big Tits | south_asian | -0.155 | 128.000 | 0.000 |
| Masturbation | south_asian | -0.131 | 128.000 | 0.001 |
| Blonde | africa | 0.130 | 380.000 | 0.000 |
| Blonde | east_asian | -0.115 | 886.000 | 0.000 |
| Masturbation | east_asian | 0.097 | 886.000 | 0.000 |
| Blonde | south_asian | -0.094 | 128.000 | 0.000 |
| Big Tits | east_asian | -0.085 | 886.000 | 0.000 |
| Amateur | east_asian | -0.081 | 886.000 | 0.000 |
| Teens | south_asian | -0.077 | 128.000 | 0.034 |

**Top 10 by Δ Equal Opportunity:**


| class | subgroup | eo_diff | n_sub | p_eo_adj |
|---|---|---|---|---|
| Cumshot | south_asian | -0.218 | 128.000 | 0.003 |
| Anal | south_asian | 0.204 | 128.000 | 0.678 |
| Blonde | east_asian | -0.200 | 886.000 | 0.991 |
| Fetish | east_asian | 0.190 | 886.000 | 0.141 |
| Amateur | africa | 0.154 | 380.000 | 0.005 |
| Masturbation | east_asian | 0.141 | 886.000 | 0.000 |
| Teens | east_asian | 0.126 | 886.000 | 0.001 |
| Big Tits | east_asian | 0.120 | 886.000 | 0.000 |
| Lesbian | east_asian | 0.109 | 886.000 | 0.107 |
| Asian | africa | -0.105 | 380.000 | 1.000 |

**Top 10 by Δ False Positive Rate:**


| class | subgroup | fpr_diff | n_sub | p_fpr_adj |
|---|---|---|---|---|
| Amateur | south_asian | -0.005 | 128.000 | 1.000 |
| Masturbation | south_asian | -0.003 | 128.000 | 1.000 |
| Fetish | africa | 0.002 | 380.000 | 0.057 |
| Group | east_asian | 0.002 | 886.000 | 0.141 |
| Cumshot | africa | 0.002 | 380.000 | 1.000 |
| Masturbation | africa | 0.001 | 380.000 | 1.000 |
| Cumshot | south_asian | -0.001 | 128.000 | 1.000 |
| Amateur | africa | 0.001 | 380.000 | 1.000 |
| Big Tits | europe | 0.001 | 1242.000 | 0.927 |
| Masturbation | east_asian | -0.001 | 886.000 | 1.000 |


#### dp_race_ethnicity

**Top 10 by Δ Demographic Parity:**


| class | subgroup | dp_diff | n_sub | p_dp_adj |
|---|---|---|---|---|
| Blonde | asian | -0.194 | 1173.000 | 0.000 |
| Blonde | latina | -0.170 | 836.000 | 0.000 |
| Masturbation | mixed_or_other | -0.157 | 1167.000 | 0.000 |
| Big Tits | asian | -0.129 | 1173.000 | 0.000 |
| Blonde | black | -0.099 | 2300.000 | 0.000 |
| Asian | asian | 0.087 | 1173.000 | 0.000 |
| Blonde | white | 0.085 | 6901.000 | 0.000 |
| Masturbation | latina | -0.084 | 836.000 | 0.000 |
| Interracial | mixed_or_other | 0.055 | 1167.000 | 0.000 |
| Big Tits | latina | 0.052 | 836.000 | 0.003 |

**Top 10 by Δ Equal Opportunity:**


| class | subgroup | eo_diff | n_sub | p_eo_adj |
|---|---|---|---|---|
| Blonde | latina | -0.376 | 836.000 | 0.000 |
| Blonde | asian | -0.311 | 1173.000 | 0.000 |
| Teens | latina | -0.232 | 836.000 | 0.000 |
| Group | latina | -0.106 | 836.000 | 0.286 |
| Group | mixed_or_other | -0.100 | 1167.000 | 0.017 |
| Blowjob | mixed_or_other | -0.100 | 1167.000 | 0.000 |
| Lesbian | latina | -0.093 | 836.000 | 0.081 |
| Fetish | asian | 0.092 | 1173.000 | 0.371 |
| Big Tits | asian | 0.091 | 1173.000 | 0.000 |
| Cumshot | latina | -0.090 | 836.000 | 0.000 |

**Top 10 by Δ False Positive Rate:**


| class | subgroup | fpr_diff | n_sub | p_fpr_adj |
|---|---|---|---|---|
| Asian | asian | 0.053 | 1173.000 | 0.000 |
| Amateur | latina | 0.007 | 836.000 | 0.002 |
| Teens | latina | 0.004 | 836.000 | 0.000 |
| Amateur | black | 0.004 | 2300.000 | 0.001 |
| Amateur | mixed_or_other | -0.003 | 1167.000 | 0.108 |
| Fetish | latina | 0.003 | 836.000 | 0.066 |
| Cumshot | latina | 0.003 | 836.000 | 0.002 |
| Masturbation | latina | 0.003 | 836.000 | 0.198 |
| Amateur | white | -0.002 | 6901.000 | 0.001 |
| Big Tits | latina | 0.002 | 836.000 | 0.169 |


#### dp_sexuality

**Top 10 by Δ Demographic Parity:**


| class | subgroup | dp_diff | n_sub | p_dp_adj |
|---|---|---|---|---|
| Blowjob | sexuality_lesbian | -0.026 | 1044.000 | 1.000 |
| Masturbation | sexuality_lesbian | 0.014 | 1044.000 | 1.000 |
| Cumshot | sexuality_lesbian | -0.014 | 1044.000 | 1.000 |
| Anal | sexuality_lesbian | -0.010 | 1044.000 | 1.000 |
| Big Tits | sexuality_lesbian | 0.006 | 1044.000 | 1.000 |
| Teens | sexuality_lesbian | 0.004 | 1044.000 | 1.000 |
| Lesbian | sexuality_lesbian | 0.002 | 1044.000 | 1.000 |
| Fetish | sexuality_lesbian | -0.002 | 1044.000 | 1.000 |
| Group | sexuality_lesbian | -0.002 | 1044.000 | 1.000 |
| Amateur | sexuality_lesbian | -0.002 | 1044.000 | 1.000 |

**Top 10 by Δ Equal Opportunity:**


| class | subgroup | eo_diff | n_sub | p_eo_adj |
|---|---|---|---|---|
| Cumshot | sexuality_lesbian | -0.682 | 1044.000 | 1.000 |
| Blowjob | sexuality_lesbian | -0.166 | 1044.000 | 1.000 |
| Group | sexuality_lesbian | 0.073 | 1044.000 | 1.000 |
| Anal | sexuality_lesbian | 0.021 | 1044.000 | 1.000 |
| Teens | sexuality_lesbian | 0.011 | 1044.000 | 1.000 |
| Amateur | sexuality_lesbian | 0.010 | 1044.000 | 1.000 |
| Fetish | sexuality_lesbian | -0.006 | 1044.000 | 1.000 |
| Blonde | sexuality_lesbian | -0.004 | 1044.000 | 1.000 |
| Masturbation | sexuality_lesbian | 0.003 | 1044.000 | 1.000 |
| Big Tits | sexuality_lesbian | 0.002 | 1044.000 | 1.000 |

**Top 10 by Δ False Positive Rate:**


| class | subgroup | fpr_diff | n_sub | p_fpr_adj |
|---|---|---|---|---|
| Anal | sexuality_lesbian | -0.001 | 1044.000 | 1.000 |
| Blowjob | sexuality_lesbian | 0.000 | 1044.000 | 1.000 |
| Masturbation | sexuality_lesbian | 0.000 | 1044.000 | 1.000 |
| Big Tits | sexuality_lesbian | 0.000 | 1044.000 | 1.000 |
| Blonde | sexuality_lesbian | 0.000 | 1044.000 | 1.000 |
| Teens | sexuality_lesbian | 0.000 | 1044.000 | 1.000 |
| Amateur | sexuality_lesbian | 0.000 | 1044.000 | 1.000 |
| Group | sexuality_lesbian | 0.000 | 1044.000 | 1.000 |
| Cumshot | sexuality_lesbian | 0.000 | 1044.000 | 1.000 |
| Asian | sexuality_lesbian | 0.000 | 1044.000 | 1.000 |


#### eo_age

**Top 10 by Δ Demographic Parity:**


| class | subgroup | dp_diff | n_sub | p_dp_adj |
|---|---|---|---|---|
| Big Tits | age_young | -0.275 | 1507.000 | 0.000 |
| Teens | age_young | 0.260 | 1507.000 | 0.000 |
| Big Tits | age_mature | 0.140 | 2954.000 | 0.000 |
| Teens | age_mature | -0.133 | 2954.000 | 0.000 |
| Blonde | age_young | -0.115 | 1507.000 | 0.000 |
| Amateur | age_young | 0.069 | 1507.000 | 0.000 |
| Blonde | age_mature | 0.059 | 2954.000 | 0.000 |
| Masturbation | age_young | -0.044 | 1507.000 | 0.000 |
| Group | age_young | -0.038 | 1507.000 | 0.000 |
| Blowjob | age_young | -0.038 | 1507.000 | 0.001 |

**Top 10 by Δ Equal Opportunity:**


| class | subgroup | eo_diff | n_sub | p_eo_adj |
|---|---|---|---|---|
| Blonde | age_young | -0.065 | 1507.000 | 0.000 |
| Cumshot | age_young | -0.056 | 1507.000 | 0.004 |
| Masturbation | age_young | -0.040 | 1507.000 | 0.000 |
| Cumshot | age_mature | 0.036 | 2954.000 | 0.004 |
| Asian | age_young | 0.034 | 1507.000 | 0.331 |
| Fetish | age_young | -0.029 | 1507.000 | 0.116 |
| Big Tits | age_young | -0.028 | 1507.000 | 0.000 |
| Asian | age_mature | -0.022 | 2954.000 | 0.331 |
| Blowjob | age_young | -0.021 | 1507.000 | 0.002 |
| Blonde | age_mature | 0.021 | 2954.000 | 0.000 |

**Top 10 by Δ False Positive Rate:**


| class | subgroup | fpr_diff | n_sub | p_fpr_adj |
|---|---|---|---|---|
| Amateur | age_young | 0.010 | 1507.000 | 0.014 |
| Amateur | age_mature | -0.004 | 2954.000 | 0.014 |
| Teens | age_young | 0.004 | 1507.000 | 0.004 |
| Fetish | age_young | 0.004 | 1507.000 | 0.084 |
| Masturbation | age_young | 0.004 | 1507.000 | 0.156 |
| Group | age_young | -0.002 | 1507.000 | 0.054 |
| Big Tits | age_mature | 0.002 | 2954.000 | 0.935 |
| Masturbation | age_mature | -0.002 | 2954.000 | 0.156 |
| Blonde | age_young | 0.002 | 1507.000 | 0.170 |
| Fetish | age_mature | -0.002 | 2954.000 | 0.084 |


#### eo_gender

**Top 10 by Δ Demographic Parity:**


| class | subgroup | dp_diff | n_sub | p_dp_adj |
|---|---|---|---|---|
| Blowjob | gender_male | 0.397 | 185.000 | 0.000 |
| Masturbation | gender_male | -0.337 | 185.000 | 0.000 |
| Cumshot | gender_male | 0.102 | 185.000 | 0.000 |
| Teens | gender_male | 0.075 | 185.000 | 0.007 |
| Group | gender_male | 0.073 | 185.000 | 0.000 |
| Blonde | gender_male | 0.066 | 185.000 | 0.060 |
| Asian | gender_male | 0.066 | 185.000 | 0.003 |
| Interracial | gender_male | 0.050 | 185.000 | 0.000 |
| Amateur | gender_male | -0.049 | 185.000 | 0.241 |
| Big Tits | gender_male | -0.038 | 185.000 | 0.513 |

**Top 10 by Δ Equal Opportunity:**


| class | subgroup | eo_diff | n_sub | p_eo_adj |
|---|---|---|---|---|
| Anal | gender_male | -0.099 | 185.000 | 0.061 |
| Blonde | gender_male | 0.067 | 185.000 | 0.143 |
| Big Tits | gender_male | -0.059 | 185.000 | 0.000 |
| Asian | gender_male | 0.052 | 185.000 | 0.339 |
| Blowjob | gender_male | 0.047 | 185.000 | 0.143 |
| Cumshot | gender_male | 0.035 | 185.000 | 1.000 |
| Masturbation | gender_male | -0.031 | 185.000 | 0.409 |
| Group | gender_male | -0.027 | 185.000 | 0.704 |
| Interracial | gender_male | 0.026 | 185.000 | 0.969 |
| Fetish | gender_male | 0.020 | 185.000 | 1.000 |

**Top 10 by Δ False Positive Rate:**


| class | subgroup | fpr_diff | n_sub | p_fpr_adj |
|---|---|---|---|---|
| Big Tits | gender_male | -0.013 | 185.000 | 0.369 |
| Cumshot | gender_male | 0.010 | 185.000 | 0.038 |
| Amateur | gender_male | -0.007 | 185.000 | 0.922 |
| Group | gender_male | 0.006 | 185.000 | 0.001 |
| Masturbation | gender_male | -0.005 | 185.000 | 0.801 |
| Anal | gender_male | 0.003 | 185.000 | 0.580 |
| Blonde | gender_male | -0.002 | 185.000 | 1.000 |
| Teens | gender_male | -0.002 | 185.000 | 1.000 |
| Fetish | gender_male | 0.001 | 185.000 | 1.000 |
| Big Tits | gender_female | 0.001 | 2274.000 | 0.369 |


#### eo_hair_color

**Top 10 by Δ Demographic Parity:**


| class | subgroup | dp_diff | n_sub | p_dp_adj |
|---|---|---|---|---|
| Blonde | blonde | 0.508 | 3954.000 | 0.000 |
| Blonde | brunette | -0.295 | 6045.000 | 0.000 |
| Blonde | redhead | -0.273 | 821.000 | 0.000 |
| Blowjob | redhead | -0.087 | 821.000 | 0.000 |
| Asian | blonde | -0.075 | 3954.000 | 0.000 |
| Big Tits | redhead | 0.074 | 821.000 | 0.000 |
| Amateur | redhead | 0.061 | 821.000 | 0.000 |
| Asian | brunette | 0.057 | 6045.000 | 0.000 |
| Asian | redhead | -0.055 | 821.000 | 0.000 |
| Masturbation | redhead | 0.045 | 821.000 | 0.019 |

**Top 10 by Δ Equal Opportunity:**


| class | subgroup | eo_diff | n_sub | p_eo_adj |
|---|---|---|---|---|
| Asian | blonde | -0.279 | 3954.000 | 0.000 |
| Asian | redhead | -0.126 | 821.000 | 0.011 |
| Blowjob | redhead | -0.037 | 821.000 | 0.000 |
| Asian | brunette | 0.020 | 6045.000 | 0.000 |
| Group | redhead | -0.017 | 821.000 | 0.383 |
| Cumshot | redhead | 0.015 | 821.000 | 0.784 |
| Group | blonde | -0.015 | 3954.000 | 0.092 |
| Masturbation | blonde | -0.014 | 3954.000 | 0.001 |
| Blonde | brunette | -0.014 | 6045.000 | 0.260 |
| Lesbian | redhead | 0.012 | 821.000 | 1.000 |

**Top 10 by Δ False Positive Rate:**


| class | subgroup | fpr_diff | n_sub | p_fpr_adj |
|---|---|---|---|---|
| Blonde | blonde | 0.115 | 3954.000 | 0.000 |
| Amateur | redhead | 0.007 | 821.000 | 0.172 |
| Teens | redhead | 0.002 | 821.000 | 0.061 |
| Fetish | redhead | 0.002 | 821.000 | 0.665 |
| Blowjob | redhead | 0.002 | 821.000 | 0.412 |
| Blonde | redhead | -0.002 | 821.000 | 0.231 |
| Anal | redhead | 0.002 | 821.000 | 0.409 |
| Anal | blonde | -0.002 | 3954.000 | 0.101 |
| Blonde | brunette | -0.001 | 6045.000 | 0.000 |
| Masturbation | blonde | -0.001 | 3954.000 | 0.529 |


#### eo_nationality

**Top 10 by Δ Demographic Parity:**


| class | subgroup | dp_diff | n_sub | p_dp_adj |
|---|---|---|---|---|
| Asian | east_asian | 0.660 | 886.000 | 0.000 |
| Blowjob | south_asian | -0.383 | 128.000 | 0.000 |
| Asian | south_asian | -0.304 | 128.000 | 0.000 |
| Asian | europe | -0.299 | 1242.000 | 0.000 |
| Asian | africa | -0.283 | 380.000 | 0.000 |
| Blonde | africa | 0.226 | 380.000 | 0.000 |
| Blonde | east_asian | -0.216 | 886.000 | 0.000 |
| Big Tits | south_asian | -0.203 | 128.000 | 0.000 |
| Blonde | south_asian | -0.174 | 128.000 | 0.000 |
| Masturbation | south_asian | -0.161 | 128.000 | 0.000 |

**Top 10 by Δ Equal Opportunity:**


| class | subgroup | eo_diff | n_sub | p_eo_adj |
|---|---|---|---|---|
| Asian | south_asian | -0.959 | 128.000 | 0.000 |
| Asian | europe | -0.497 | 1242.000 | 0.000 |
| Blonde | east_asian | -0.199 | 886.000 | 0.139 |
| Cumshot | south_asian | -0.190 | 128.000 | 0.175 |
| Asian | africa | -0.159 | 380.000 | 0.006 |
| Lesbian | south_asian | -0.109 | 128.000 | 0.347 |
| Teens | south_asian | -0.088 | 128.000 | 0.008 |
| Blonde | south_asian | 0.087 | 128.000 | 1.000 |
| Anal | south_asian | 0.061 | 128.000 | 1.000 |
| Cumshot | east_asian | 0.036 | 886.000 | 1.000 |

**Top 10 by Δ False Positive Rate:**


| class | subgroup | fpr_diff | n_sub | p_fpr_adj |
|---|---|---|---|---|
| Asian | east_asian | 0.099 | 886.000 | 0.000 |
| Amateur | south_asian | -0.010 | 128.000 | 0.522 |
| Amateur | europe | 0.006 | 1242.000 | 0.236 |
| Fetish | south_asian | 0.005 | 128.000 | 0.605 |
| Big Tits | europe | 0.005 | 1242.000 | 0.030 |
| Big Tits | east_asian | -0.005 | 886.000 | 0.063 |
| Big Tits | africa | -0.005 | 380.000 | 0.559 |
| Big Tits | south_asian | 0.004 | 128.000 | 0.559 |
| Amateur | east_asian | -0.004 | 886.000 | 0.331 |
| Masturbation | south_asian | 0.004 | 128.000 | 1.000 |


#### eo_race_ethnicity

**Top 10 by Δ Demographic Parity:**


| class | subgroup | dp_diff | n_sub | p_dp_adj |
|---|---|---|---|---|
| Asian | asian | 0.813 | 1173.000 | 0.000 |
| Interracial | mixed_or_other | 0.665 | 1167.000 | 0.000 |
| Blonde | asian | -0.287 | 1173.000 | 0.000 |
| Blonde | latina | -0.189 | 836.000 | 0.000 |
| Masturbation | mixed_or_other | -0.186 | 1167.000 | 0.000 |
| Big Tits | asian | -0.186 | 1173.000 | 0.000 |
| Interracial | asian | -0.176 | 1173.000 | 0.000 |
| Blonde | black | -0.133 | 2300.000 | 0.000 |
| Interracial | black | 0.115 | 2300.000 | 0.000 |
| Blonde | white | 0.113 | 6901.000 | 0.000 |

**Top 10 by Δ Equal Opportunity:**


| class | subgroup | eo_diff | n_sub | p_eo_adj |
|---|---|---|---|---|
| Asian | latina | -0.467 | 836.000 | 0.000 |
| Asian | white | -0.359 | 6901.000 | 0.000 |
| Asian | mixed_or_other | -0.229 | 1167.000 | 0.000 |
| Blonde | asian | -0.138 | 1173.000 | 0.000 |
| Lesbian | mixed_or_other | -0.087 | 1167.000 | 0.002 |
| Blonde | latina | -0.082 | 836.000 | 0.000 |
| Masturbation | mixed_or_other | -0.074 | 1167.000 | 0.000 |
| Interracial | asian | -0.040 | 1173.000 | 0.183 |
| Asian | asian | 0.031 | 1173.000 | 0.000 |
| Blonde | black | -0.031 | 2300.000 | 0.000 |

**Top 10 by Δ False Positive Rate:**


| class | subgroup | fpr_diff | n_sub | p_fpr_adj |
|---|---|---|---|---|
| Asian | asian | 0.105 | 1173.000 | 0.000 |
| Interracial | mixed_or_other | 0.021 | 1167.000 | 0.000 |
| Amateur | latina | 0.010 | 836.000 | 0.000 |
| Amateur | black | 0.007 | 2300.000 | 0.000 |
| Big Tits | latina | 0.006 | 836.000 | 0.187 |
| Big Tits | black | 0.006 | 2300.000 | 0.004 |
| Group | mixed_or_other | 0.006 | 1167.000 | 0.002 |
| Big Tits | asian | -0.006 | 1173.000 | 0.072 |
| Teens | latina | 0.004 | 836.000 | 0.000 |
| Fetish | latina | 0.004 | 836.000 | 0.021 |


#### eo_sexuality

**Top 10 by Δ Demographic Parity:**


| class | subgroup | dp_diff | n_sub | p_dp_adj |
|---|---|---|---|---|
| Lesbian | sexuality_lesbian | 0.044 | 1044.000 | 1.000 |
| Blowjob | sexuality_lesbian | -0.031 | 1044.000 | 1.000 |
| Masturbation | sexuality_lesbian | 0.021 | 1044.000 | 1.000 |
| Anal | sexuality_lesbian | -0.016 | 1044.000 | 1.000 |
| Group | sexuality_lesbian | -0.015 | 1044.000 | 1.000 |
| Cumshot | sexuality_lesbian | -0.015 | 1044.000 | 1.000 |
| Big Tits | sexuality_lesbian | 0.005 | 1044.000 | 1.000 |
| Blonde | sexuality_lesbian | 0.005 | 1044.000 | 1.000 |
| Amateur | sexuality_lesbian | -0.004 | 1044.000 | 1.000 |
| Interracial | sexuality_lesbian | 0.003 | 1044.000 | 1.000 |

**Top 10 by Δ Equal Opportunity:**


| class | subgroup | eo_diff | n_sub | p_eo_adj |
|---|---|---|---|---|
| Cumshot | sexuality_lesbian | -0.573 | 1044.000 | 1.000 |
| Blowjob | sexuality_lesbian | -0.068 | 1044.000 | 1.000 |
| Group | sexuality_lesbian | -0.067 | 1044.000 | 1.000 |
| Asian | sexuality_lesbian | 0.009 | 1044.000 | 1.000 |
| Fetish | sexuality_lesbian | 0.006 | 1044.000 | 1.000 |
| Anal | sexuality_lesbian | 0.004 | 1044.000 | 1.000 |
| Blonde | sexuality_lesbian | 0.003 | 1044.000 | 1.000 |
| Amateur | sexuality_lesbian | -0.001 | 1044.000 | 1.000 |
| Masturbation | sexuality_lesbian | 0.001 | 1044.000 | 1.000 |
| Big Tits | sexuality_lesbian | -0.000 | 1044.000 | 1.000 |

**Top 10 by Δ False Positive Rate:**


| class | subgroup | fpr_diff | n_sub | p_fpr_adj |
|---|---|---|---|---|
| Lesbian | sexuality_lesbian | 0.029 | 1044.000 | 1.000 |
| Big Tits | sexuality_lesbian | -0.002 | 1044.000 | 1.000 |
| Amateur | sexuality_lesbian | -0.001 | 1044.000 | 1.000 |
| Group | sexuality_lesbian | -0.001 | 1044.000 | 1.000 |
| Anal | sexuality_lesbian | -0.001 | 1044.000 | 1.000 |
| Blonde | sexuality_lesbian | 0.000 | 1044.000 | 1.000 |
| Fetish | sexuality_lesbian | 0.000 | 1044.000 | 1.000 |
| Blowjob | sexuality_lesbian | 0.000 | 1044.000 | 1.000 |
| Masturbation | sexuality_lesbian | 0.000 | 1044.000 | 1.000 |
| Teens | sexuality_lesbian | 0.000 | 1044.000 | 1.000 |


#### gender

**Top 10 by Δ Demographic Parity:**


| class | subgroup | dp_diff | n_sub | p_dp_adj |
|---|---|---|---|---|
| Blowjob | gender_male | 0.411 | 185.000 | 0.000 |
| Masturbation | gender_male | -0.347 | 185.000 | 0.000 |
| Cumshot | gender_male | 0.123 | 185.000 | 0.000 |
| Teens | gender_male | 0.079 | 185.000 | 0.005 |
| Group | gender_male | 0.076 | 185.000 | 0.000 |
| Asian | gender_male | 0.062 | 185.000 | 0.007 |
| Blonde | gender_male | 0.049 | 185.000 | 0.245 |
| Interracial | gender_male | 0.048 | 185.000 | 0.000 |
| Lesbian | gender_male | -0.036 | 185.000 | 0.012 |
| Blowjob | gender_female | -0.033 | 2274.000 | 0.000 |

**Top 10 by Δ Equal Opportunity:**


| class | subgroup | eo_diff | n_sub | p_eo_adj |
|---|---|---|---|---|
| Cumshot | gender_male | 0.090 | 185.000 | 0.161 |
| Anal | gender_male | -0.047 | 185.000 | 0.355 |
| Blowjob | gender_male | 0.040 | 185.000 | 0.102 |
| Group | gender_male | -0.039 | 185.000 | 0.127 |
| Big Tits | gender_male | -0.037 | 185.000 | 0.002 |
| Masturbation | gender_male | -0.035 | 185.000 | 0.050 |
| Cumshot | gender_female | -0.028 | 2274.000 | 0.161 |
| Fetish | gender_male | 0.013 | 185.000 | 1.000 |
| Group | gender_female | 0.011 | 2274.000 | 0.127 |
| Blonde | gender_male | 0.009 | 185.000 | 1.000 |

**Top 10 by Δ False Positive Rate:**


| class | subgroup | fpr_diff | n_sub | p_fpr_adj |
|---|---|---|---|---|
| Amateur | gender_male | 0.014 | 185.000 | 0.416 |
| Masturbation | gender_male | -0.011 | 185.000 | 0.412 |
| Group | gender_male | 0.010 | 185.000 | 0.007 |
| Cumshot | gender_male | 0.010 | 185.000 | 0.038 |
| Big Tits | gender_male | -0.009 | 185.000 | 0.876 |
| Blonde | gender_male | -0.006 | 185.000 | 0.723 |
| Teens | gender_male | -0.002 | 185.000 | 1.000 |
| Masturbation | gender_female | 0.002 | 2274.000 | 0.412 |
| Fetish | gender_male | 0.001 | 185.000 | 1.000 |
| Interracial | gender_male | -0.001 | 185.000 | 1.000 |


#### hair_color

**Top 10 by Δ Demographic Parity:**


| class | subgroup | dp_diff | n_sub | p_dp_adj |
|---|---|---|---|---|
| Blonde | blonde | 0.538 | 3954.000 | 0.000 |
| Blonde | brunette | -0.313 | 6045.000 | 0.000 |
| Blonde | redhead | -0.288 | 821.000 | 0.000 |
| Blowjob | redhead | -0.082 | 821.000 | 0.000 |
| Asian | blonde | -0.078 | 3954.000 | 0.000 |
| Big Tits | redhead | 0.076 | 821.000 | 0.000 |
| Amateur | redhead | 0.062 | 821.000 | 0.000 |
| Asian | brunette | 0.059 | 6045.000 | 0.000 |
| Asian | redhead | -0.055 | 821.000 | 0.000 |
| Masturbation | redhead | 0.046 | 821.000 | 0.016 |

**Top 10 by Δ Equal Opportunity:**


| class | subgroup | eo_diff | n_sub | p_eo_adj |
|---|---|---|---|---|
| Asian | blonde | -0.125 | 3954.000 | 0.000 |
| Blowjob | redhead | -0.023 | 821.000 | 0.000 |
| Asian | redhead | -0.019 | 821.000 | 0.394 |
| Group | blonde | -0.018 | 3954.000 | 0.016 |
| Cumshot | blonde | -0.017 | 3954.000 | 0.050 |
| Fetish | redhead | 0.016 | 821.000 | 1.000 |
| Masturbation | blonde | -0.016 | 3954.000 | 0.000 |
| Blonde | redhead | -0.015 | 821.000 | 0.190 |
| Blonde | brunette | -0.012 | 6045.000 | 0.007 |
| Cumshot | brunette | 0.012 | 6045.000 | 0.051 |

**Top 10 by Δ False Positive Rate:**


| class | subgroup | fpr_diff | n_sub | p_fpr_adj |
|---|---|---|---|---|
| Blonde | blonde | 0.537 | 3954.000 | 0.000 |
| Blonde | brunette | -0.007 | 6045.000 | 0.000 |
| Amateur | redhead | 0.007 | 821.000 | 0.138 |
| Masturbation | redhead | -0.004 | 821.000 | 0.327 |
| Blonde | redhead | -0.003 | 821.000 | 0.361 |
| Big Tits | redhead | 0.003 | 821.000 | 1.000 |
| Fetish | redhead | 0.003 | 821.000 | 0.678 |
| Teens | redhead | 0.002 | 821.000 | 0.061 |
| Masturbation | blonde | -0.002 | 3954.000 | 0.292 |
| Anal | blonde | -0.002 | 3954.000 | 0.116 |


#### nationality

**Top 10 by Δ Demographic Parity:**


| class | subgroup | dp_diff | n_sub | p_dp_adj |
|---|---|---|---|---|
| Asian | east_asian | 0.676 | 886.000 | 0.000 |
| Blowjob | south_asian | -0.394 | 128.000 | 0.000 |
| Asian | south_asian | -0.309 | 128.000 | 0.000 |
| Asian | europe | -0.307 | 1242.000 | 0.000 |
| Asian | africa | -0.290 | 380.000 | 0.000 |
| Blonde | africa | 0.236 | 380.000 | 0.000 |
| Blonde | east_asian | -0.232 | 886.000 | 0.000 |
| Big Tits | south_asian | -0.207 | 128.000 | 0.000 |
| Blonde | south_asian | -0.193 | 128.000 | 0.000 |
| Masturbation | south_asian | -0.172 | 128.000 | 0.000 |

**Top 10 by Δ Equal Opportunity:**


| class | subgroup | eo_diff | n_sub | p_eo_adj |
|---|---|---|---|---|
| Cumshot | south_asian | -0.242 | 128.000 | 0.000 |
| Asian | europe | -0.149 | 1242.000 | 0.000 |
| Teens | south_asian | -0.090 | 128.000 | 0.008 |
| Anal | south_asian | 0.047 | 128.000 | 1.000 |
| Cumshot | east_asian | 0.044 | 886.000 | 0.297 |
| Interracial | europe | -0.023 | 1242.000 | 0.645 |
| Amateur | south_asian | -0.022 | 128.000 | 1.000 |
| Anal | africa | 0.021 | 380.000 | 1.000 |
| Amateur | east_asian | 0.019 | 886.000 | 0.900 |
| Cumshot | europe | 0.019 | 1242.000 | 1.000 |

**Top 10 by Δ False Positive Rate:**


| class | subgroup | fpr_diff | n_sub | p_fpr_adj |
|---|---|---|---|---|
| Asian | east_asian | 0.298 | 886.000 | 0.000 |
| Group | east_asian | 0.016 | 886.000 | 0.000 |
| Amateur | south_asian | -0.014 | 128.000 | 0.397 |
| Group | south_asian | -0.007 | 128.000 | 0.428 |
| Amateur | europe | 0.007 | 1242.000 | 0.060 |
| Big Tits | east_asian | -0.007 | 886.000 | 0.013 |
| Amateur | east_asian | -0.007 | 886.000 | 0.129 |
| Group | europe | -0.007 | 1242.000 | 0.001 |
| Big Tits | europe | 0.006 | 1242.000 | 0.026 |
| Group | africa | -0.005 | 380.000 | 0.428 |


#### race_ethnicity

**Top 10 by Δ Demographic Parity:**


| class | subgroup | dp_diff | n_sub | p_dp_adj |
|---|---|---|---|---|
| Asian | asian | 0.872 | 1173.000 | 0.000 |
| Interracial | mixed_or_other | 0.680 | 1167.000 | 0.000 |
| Blonde | asian | -0.290 | 1173.000 | 0.000 |
| Masturbation | mixed_or_other | -0.189 | 1167.000 | 0.000 |
| Big Tits | asian | -0.187 | 1173.000 | 0.000 |
| Blonde | latina | -0.179 | 836.000 | 0.000 |
| Interracial | asian | -0.178 | 1173.000 | 0.000 |
| Blonde | black | -0.134 | 2300.000 | 0.000 |
| Interracial | black | 0.116 | 2300.000 | 0.000 |
| Blonde | white | 0.112 | 6901.000 | 0.000 |

**Top 10 by Δ Equal Opportunity:**


| class | subgroup | eo_diff | n_sub | p_eo_adj |
|---|---|---|---|---|
| Asian | latina | -0.265 | 836.000 | 0.000 |
| Asian | mixed_or_other | -0.146 | 1167.000 | 0.000 |
| Asian | white | -0.109 | 6901.000 | 0.000 |
| Masturbation | mixed_or_other | -0.074 | 1167.000 | 0.000 |
| Blonde | asian | -0.043 | 1173.000 | 0.025 |
| Cumshot | latina | -0.042 | 836.000 | 0.055 |
| Group | mixed_or_other | -0.030 | 1167.000 | 0.094 |
| Group | latina | 0.026 | 836.000 | 0.785 |
| Fetish | mixed_or_other | -0.025 | 1167.000 | 0.338 |
| Blonde | black | -0.021 | 2300.000 | 0.000 |

**Top 10 by Δ False Positive Rate:**


| class | subgroup | fpr_diff | n_sub | p_fpr_adj |
|---|---|---|---|---|
| Asian | asian | 0.525 | 1173.000 | 0.000 |
| Interracial | mixed_or_other | 0.098 | 1167.000 | 0.000 |
| Group | asian | 0.012 | 1173.000 | 0.000 |
| Amateur | latina | 0.011 | 836.000 | 0.000 |
| Masturbation | asian | 0.008 | 1173.000 | 0.003 |
| Amateur | black | 0.008 | 2300.000 | 0.000 |
| Big Tits | asian | -0.007 | 1173.000 | 0.027 |
| Big Tits | black | 0.007 | 2300.000 | 0.006 |
| Big Tits | latina | 0.005 | 836.000 | 0.540 |
| Teens | latina | 0.004 | 836.000 | 0.000 |


#### sexuality

**Top 10 by Δ Demographic Parity:**


| class | subgroup | dp_diff | n_sub | p_dp_adj |
|---|---|---|---|---|
| Lesbian | sexuality_lesbian | 0.045 | 1044.000 | 1.000 |
| Blowjob | sexuality_lesbian | -0.032 | 1044.000 | 1.000 |
| Masturbation | sexuality_lesbian | 0.021 | 1044.000 | 1.000 |
| Anal | sexuality_lesbian | -0.016 | 1044.000 | 1.000 |
| Group | sexuality_lesbian | -0.015 | 1044.000 | 1.000 |
| Cumshot | sexuality_lesbian | -0.014 | 1044.000 | 1.000 |
| Big Tits | sexuality_lesbian | 0.006 | 1044.000 | 1.000 |
| Amateur | sexuality_lesbian | -0.004 | 1044.000 | 1.000 |
| Blonde | sexuality_lesbian | 0.003 | 1044.000 | 1.000 |
| Interracial | sexuality_lesbian | 0.003 | 1044.000 | 1.000 |

**Top 10 by Δ Equal Opportunity:**


| class | subgroup | eo_diff | n_sub | p_eo_adj |
|---|---|---|---|---|
| Cumshot | sexuality_lesbian | -0.264 | 1044.000 | 1.000 |
| Blowjob | sexuality_lesbian | -0.082 | 1044.000 | 1.000 |
| Group | sexuality_lesbian | -0.049 | 1044.000 | 1.000 |
| Anal | sexuality_lesbian | 0.008 | 1044.000 | 1.000 |
| Asian | sexuality_lesbian | -0.002 | 1044.000 | 1.000 |
| Fetish | sexuality_lesbian | -0.001 | 1044.000 | 1.000 |
| Amateur | sexuality_lesbian | -0.001 | 1044.000 | 1.000 |
| Big Tits | sexuality_lesbian | -0.000 | 1044.000 | 1.000 |
| Blonde | sexuality_lesbian | -0.000 | 1044.000 | 1.000 |
| Teens | sexuality_lesbian | -0.000 | 1044.000 | 1.000 |

**Top 10 by Δ False Positive Rate:**


| class | subgroup | fpr_diff | n_sub | p_fpr_adj |
|---|---|---|---|---|
| Lesbian | sexuality_lesbian | 0.230 | 1044.000 | 1.000 |
| Masturbation | sexuality_lesbian | 0.002 | 1044.000 | 1.000 |
| Big Tits | sexuality_lesbian | -0.001 | 1044.000 | 1.000 |
| Blonde | sexuality_lesbian | -0.001 | 1044.000 | 1.000 |
| Amateur | sexuality_lesbian | -0.001 | 1044.000 | 1.000 |
| Group | sexuality_lesbian | -0.001 | 1044.000 | 1.000 |
| Anal | sexuality_lesbian | -0.001 | 1044.000 | 1.000 |
| Fetish | sexuality_lesbian | 0.000 | 1044.000 | 1.000 |
| Interracial | sexuality_lesbian | 0.000 | 1044.000 | 1.000 |
| Asian | sexuality_lesbian | 0.000 | 1044.000 | 1.000 |



### Model: `lr_eo`

**Number of significant subgroup gaps by metric (Holm-adj):**


| namespace | metric | n_significant |
|---|---|---|
| age | DP | 20 |
| age | EO | 10 |
| age | FPR | 4 |
| gender | DP | 16 |
| gender | EO | 2 |
| gender | FPR | 4 |
| hair_color | DP | 20 |
| hair_color | EO | 7 |
| hair_color | FPR | 2 |
| nationality | DP | 39 |
| nationality | EO | 7 |
| nationality | FPR | 2 |
| race_ethnicity | DP | 47 |
| race_ethnicity | EO | 15 |
| race_ethnicity | FPR | 12 |
| sexuality | DP | 0 |
| sexuality | EO | 0 |
| sexuality | FPR | 0 |


#### age

**Top 10 by Δ Demographic Parity:**


| class | subgroup | dp_diff | n_sub | p_dp_adj |
|---|---|---|---|---|
| Big Tits | age_young | -0.275 | 1507.000 | 0.000 |
| Teens | age_young | 0.260 | 1507.000 | 0.000 |
| Big Tits | age_mature | 0.140 | 2954.000 | 0.000 |
| Teens | age_mature | -0.133 | 2954.000 | 0.000 |
| Blonde | age_young | -0.115 | 1507.000 | 0.000 |
| Amateur | age_young | 0.069 | 1507.000 | 0.000 |
| Blonde | age_mature | 0.059 | 2954.000 | 0.000 |
| Masturbation | age_young | -0.044 | 1507.000 | 0.000 |
| Group | age_young | -0.038 | 1507.000 | 0.000 |
| Blowjob | age_young | -0.038 | 1507.000 | 0.001 |

**Top 10 by Δ Equal Opportunity:**


| class | subgroup | eo_diff | n_sub | p_eo_adj |
|---|---|---|---|---|
| Blonde | age_young | -0.065 | 1507.000 | 0.000 |
| Cumshot | age_young | -0.056 | 1507.000 | 0.004 |
| Masturbation | age_young | -0.040 | 1507.000 | 0.000 |
| Cumshot | age_mature | 0.036 | 2954.000 | 0.004 |
| Asian | age_young | 0.034 | 1507.000 | 0.331 |
| Fetish | age_young | -0.029 | 1507.000 | 0.116 |
| Big Tits | age_young | -0.028 | 1507.000 | 0.000 |
| Asian | age_mature | -0.022 | 2954.000 | 0.331 |
| Blowjob | age_young | -0.021 | 1507.000 | 0.002 |
| Blonde | age_mature | 0.021 | 2954.000 | 0.000 |

**Top 10 by Δ False Positive Rate:**


| class | subgroup | fpr_diff | n_sub | p_fpr_adj |
|---|---|---|---|---|
| Amateur | age_young | 0.010 | 1507.000 | 0.014 |
| Amateur | age_mature | -0.004 | 2954.000 | 0.014 |
| Teens | age_young | 0.004 | 1507.000 | 0.004 |
| Fetish | age_young | 0.004 | 1507.000 | 0.084 |
| Masturbation | age_young | 0.004 | 1507.000 | 0.156 |
| Group | age_young | -0.002 | 1507.000 | 0.054 |
| Big Tits | age_mature | 0.002 | 2954.000 | 0.935 |
| Masturbation | age_mature | -0.002 | 2954.000 | 0.156 |
| Blonde | age_young | 0.002 | 1507.000 | 0.170 |
| Fetish | age_mature | -0.002 | 2954.000 | 0.084 |


#### gender

**Top 10 by Δ Demographic Parity:**


| class | subgroup | dp_diff | n_sub | p_dp_adj |
|---|---|---|---|---|
| Blowjob | gender_male | 0.397 | 185.000 | 0.000 |
| Masturbation | gender_male | -0.337 | 185.000 | 0.000 |
| Cumshot | gender_male | 0.102 | 185.000 | 0.000 |
| Teens | gender_male | 0.075 | 185.000 | 0.007 |
| Group | gender_male | 0.073 | 185.000 | 0.000 |
| Blonde | gender_male | 0.066 | 185.000 | 0.060 |
| Asian | gender_male | 0.066 | 185.000 | 0.003 |
| Interracial | gender_male | 0.050 | 185.000 | 0.000 |
| Amateur | gender_male | -0.049 | 185.000 | 0.241 |
| Big Tits | gender_male | -0.038 | 185.000 | 0.513 |

**Top 10 by Δ Equal Opportunity:**


| class | subgroup | eo_diff | n_sub | p_eo_adj |
|---|---|---|---|---|
| Anal | gender_male | -0.099 | 185.000 | 0.061 |
| Blonde | gender_male | 0.067 | 185.000 | 0.143 |
| Big Tits | gender_male | -0.059 | 185.000 | 0.000 |
| Asian | gender_male | 0.052 | 185.000 | 0.339 |
| Blowjob | gender_male | 0.047 | 185.000 | 0.143 |
| Cumshot | gender_male | 0.035 | 185.000 | 1.000 |
| Masturbation | gender_male | -0.031 | 185.000 | 0.409 |
| Group | gender_male | -0.027 | 185.000 | 0.704 |
| Interracial | gender_male | 0.026 | 185.000 | 0.969 |
| Fetish | gender_male | 0.020 | 185.000 | 1.000 |

**Top 10 by Δ False Positive Rate:**


| class | subgroup | fpr_diff | n_sub | p_fpr_adj |
|---|---|---|---|---|
| Big Tits | gender_male | -0.013 | 185.000 | 0.369 |
| Cumshot | gender_male | 0.010 | 185.000 | 0.038 |
| Amateur | gender_male | -0.007 | 185.000 | 0.922 |
| Group | gender_male | 0.006 | 185.000 | 0.001 |
| Masturbation | gender_male | -0.005 | 185.000 | 0.801 |
| Anal | gender_male | 0.003 | 185.000 | 0.580 |
| Blonde | gender_male | -0.002 | 185.000 | 1.000 |
| Teens | gender_male | -0.002 | 185.000 | 1.000 |
| Fetish | gender_male | 0.001 | 185.000 | 1.000 |
| Big Tits | gender_female | 0.001 | 2274.000 | 0.369 |


#### hair_color

**Top 10 by Δ Demographic Parity:**


| class | subgroup | dp_diff | n_sub | p_dp_adj |
|---|---|---|---|---|
| Blonde | blonde | 0.508 | 3954.000 | 0.000 |
| Blonde | brunette | -0.295 | 6045.000 | 0.000 |
| Blonde | redhead | -0.273 | 821.000 | 0.000 |
| Blowjob | redhead | -0.087 | 821.000 | 0.000 |
| Asian | blonde | -0.075 | 3954.000 | 0.000 |
| Big Tits | redhead | 0.074 | 821.000 | 0.000 |
| Amateur | redhead | 0.061 | 821.000 | 0.000 |
| Asian | brunette | 0.057 | 6045.000 | 0.000 |
| Asian | redhead | -0.055 | 821.000 | 0.000 |
| Masturbation | redhead | 0.045 | 821.000 | 0.019 |

**Top 10 by Δ Equal Opportunity:**


| class | subgroup | eo_diff | n_sub | p_eo_adj |
|---|---|---|---|---|
| Asian | blonde | -0.279 | 3954.000 | 0.000 |
| Asian | redhead | -0.126 | 821.000 | 0.011 |
| Blowjob | redhead | -0.037 | 821.000 | 0.000 |
| Asian | brunette | 0.020 | 6045.000 | 0.000 |
| Group | redhead | -0.017 | 821.000 | 0.383 |
| Cumshot | redhead | 0.015 | 821.000 | 0.784 |
| Group | blonde | -0.015 | 3954.000 | 0.092 |
| Masturbation | blonde | -0.014 | 3954.000 | 0.001 |
| Blonde | brunette | -0.014 | 6045.000 | 0.260 |
| Lesbian | redhead | 0.012 | 821.000 | 1.000 |

**Top 10 by Δ False Positive Rate:**


| class | subgroup | fpr_diff | n_sub | p_fpr_adj |
|---|---|---|---|---|
| Blonde | blonde | 0.115 | 3954.000 | 0.000 |
| Amateur | redhead | 0.007 | 821.000 | 0.172 |
| Teens | redhead | 0.002 | 821.000 | 0.061 |
| Fetish | redhead | 0.002 | 821.000 | 0.665 |
| Blowjob | redhead | 0.002 | 821.000 | 0.412 |
| Blonde | redhead | -0.002 | 821.000 | 0.231 |
| Anal | redhead | 0.002 | 821.000 | 0.409 |
| Anal | blonde | -0.002 | 3954.000 | 0.101 |
| Blonde | brunette | -0.001 | 6045.000 | 0.000 |
| Masturbation | blonde | -0.001 | 3954.000 | 0.529 |


#### nationality

**Top 10 by Δ Demographic Parity:**


| class | subgroup | dp_diff | n_sub | p_dp_adj |
|---|---|---|---|---|
| Asian | east_asian | 0.660 | 886.000 | 0.000 |
| Blowjob | south_asian | -0.383 | 128.000 | 0.000 |
| Asian | south_asian | -0.304 | 128.000 | 0.000 |
| Asian | europe | -0.299 | 1242.000 | 0.000 |
| Asian | africa | -0.283 | 380.000 | 0.000 |
| Blonde | africa | 0.226 | 380.000 | 0.000 |
| Blonde | east_asian | -0.216 | 886.000 | 0.000 |
| Big Tits | south_asian | -0.203 | 128.000 | 0.000 |
| Blonde | south_asian | -0.174 | 128.000 | 0.000 |
| Masturbation | south_asian | -0.161 | 128.000 | 0.000 |

**Top 10 by Δ Equal Opportunity:**


| class | subgroup | eo_diff | n_sub | p_eo_adj |
|---|---|---|---|---|
| Asian | south_asian | -0.959 | 128.000 | 0.000 |
| Asian | europe | -0.497 | 1242.000 | 0.000 |
| Blonde | east_asian | -0.199 | 886.000 | 0.139 |
| Cumshot | south_asian | -0.190 | 128.000 | 0.175 |
| Asian | africa | -0.159 | 380.000 | 0.006 |
| Lesbian | south_asian | -0.109 | 128.000 | 0.347 |
| Teens | south_asian | -0.088 | 128.000 | 0.008 |
| Blonde | south_asian | 0.087 | 128.000 | 1.000 |
| Anal | south_asian | 0.061 | 128.000 | 1.000 |
| Cumshot | east_asian | 0.036 | 886.000 | 1.000 |

**Top 10 by Δ False Positive Rate:**


| class | subgroup | fpr_diff | n_sub | p_fpr_adj |
|---|---|---|---|---|
| Asian | east_asian | 0.099 | 886.000 | 0.000 |
| Amateur | south_asian | -0.010 | 128.000 | 0.522 |
| Amateur | europe | 0.006 | 1242.000 | 0.236 |
| Fetish | south_asian | 0.005 | 128.000 | 0.605 |
| Big Tits | europe | 0.005 | 1242.000 | 0.030 |
| Big Tits | east_asian | -0.005 | 886.000 | 0.063 |
| Big Tits | africa | -0.005 | 380.000 | 0.559 |
| Big Tits | south_asian | 0.004 | 128.000 | 0.559 |
| Amateur | east_asian | -0.004 | 886.000 | 0.331 |
| Masturbation | south_asian | 0.004 | 128.000 | 1.000 |


#### race_ethnicity

**Top 10 by Δ Demographic Parity:**


| class | subgroup | dp_diff | n_sub | p_dp_adj |
|---|---|---|---|---|
| Asian | asian | 0.813 | 1173.000 | 0.000 |
| Interracial | mixed_or_other | 0.665 | 1167.000 | 0.000 |
| Blonde | asian | -0.287 | 1173.000 | 0.000 |
| Blonde | latina | -0.189 | 836.000 | 0.000 |
| Masturbation | mixed_or_other | -0.186 | 1167.000 | 0.000 |
| Big Tits | asian | -0.186 | 1173.000 | 0.000 |
| Interracial | asian | -0.176 | 1173.000 | 0.000 |
| Blonde | black | -0.133 | 2300.000 | 0.000 |
| Interracial | black | 0.115 | 2300.000 | 0.000 |
| Blonde | white | 0.113 | 6901.000 | 0.000 |

**Top 10 by Δ Equal Opportunity:**


| class | subgroup | eo_diff | n_sub | p_eo_adj |
|---|---|---|---|---|
| Asian | latina | -0.467 | 836.000 | 0.000 |
| Asian | white | -0.359 | 6901.000 | 0.000 |
| Asian | mixed_or_other | -0.229 | 1167.000 | 0.000 |
| Blonde | asian | -0.138 | 1173.000 | 0.000 |
| Lesbian | mixed_or_other | -0.087 | 1167.000 | 0.002 |
| Blonde | latina | -0.082 | 836.000 | 0.000 |
| Masturbation | mixed_or_other | -0.074 | 1167.000 | 0.000 |
| Interracial | asian | -0.040 | 1173.000 | 0.183 |
| Asian | asian | 0.031 | 1173.000 | 0.000 |
| Blonde | black | -0.031 | 2300.000 | 0.000 |

**Top 10 by Δ False Positive Rate:**


| class | subgroup | fpr_diff | n_sub | p_fpr_adj |
|---|---|---|---|---|
| Asian | asian | 0.105 | 1173.000 | 0.000 |
| Interracial | mixed_or_other | 0.021 | 1167.000 | 0.000 |
| Amateur | latina | 0.010 | 836.000 | 0.000 |
| Amateur | black | 0.007 | 2300.000 | 0.000 |
| Big Tits | latina | 0.006 | 836.000 | 0.187 |
| Big Tits | black | 0.006 | 2300.000 | 0.004 |
| Group | mixed_or_other | 0.006 | 1167.000 | 0.002 |
| Big Tits | asian | -0.006 | 1173.000 | 0.072 |
| Teens | latina | 0.004 | 836.000 | 0.000 |
| Fetish | latina | 0.004 | 836.000 | 0.021 |


#### sexuality

**Top 10 by Δ Demographic Parity:**


| class | subgroup | dp_diff | n_sub | p_dp_adj |
|---|---|---|---|---|
| Lesbian | sexuality_lesbian | 0.044 | 1044.000 | 1.000 |
| Blowjob | sexuality_lesbian | -0.031 | 1044.000 | 1.000 |
| Masturbation | sexuality_lesbian | 0.021 | 1044.000 | 1.000 |
| Anal | sexuality_lesbian | -0.016 | 1044.000 | 1.000 |
| Group | sexuality_lesbian | -0.015 | 1044.000 | 1.000 |
| Cumshot | sexuality_lesbian | -0.015 | 1044.000 | 1.000 |
| Big Tits | sexuality_lesbian | 0.005 | 1044.000 | 1.000 |
| Blonde | sexuality_lesbian | 0.005 | 1044.000 | 1.000 |
| Amateur | sexuality_lesbian | -0.004 | 1044.000 | 1.000 |
| Interracial | sexuality_lesbian | 0.003 | 1044.000 | 1.000 |

**Top 10 by Δ Equal Opportunity:**


| class | subgroup | eo_diff | n_sub | p_eo_adj |
|---|---|---|---|---|
| Cumshot | sexuality_lesbian | -0.573 | 1044.000 | 1.000 |
| Blowjob | sexuality_lesbian | -0.068 | 1044.000 | 1.000 |
| Group | sexuality_lesbian | -0.067 | 1044.000 | 1.000 |
| Asian | sexuality_lesbian | 0.009 | 1044.000 | 1.000 |
| Fetish | sexuality_lesbian | 0.006 | 1044.000 | 1.000 |
| Anal | sexuality_lesbian | 0.004 | 1044.000 | 1.000 |
| Blonde | sexuality_lesbian | 0.003 | 1044.000 | 1.000 |
| Amateur | sexuality_lesbian | -0.001 | 1044.000 | 1.000 |
| Masturbation | sexuality_lesbian | 0.001 | 1044.000 | 1.000 |
| Big Tits | sexuality_lesbian | -0.000 | 1044.000 | 1.000 |

**Top 10 by Δ False Positive Rate:**


| class | subgroup | fpr_diff | n_sub | p_fpr_adj |
|---|---|---|---|---|
| Lesbian | sexuality_lesbian | 0.029 | 1044.000 | 1.000 |
| Big Tits | sexuality_lesbian | -0.002 | 1044.000 | 1.000 |
| Amateur | sexuality_lesbian | -0.001 | 1044.000 | 1.000 |
| Group | sexuality_lesbian | -0.001 | 1044.000 | 1.000 |
| Anal | sexuality_lesbian | -0.001 | 1044.000 | 1.000 |
| Blonde | sexuality_lesbian | 0.000 | 1044.000 | 1.000 |
| Fetish | sexuality_lesbian | 0.000 | 1044.000 | 1.000 |
| Blowjob | sexuality_lesbian | 0.000 | 1044.000 | 1.000 |
| Masturbation | sexuality_lesbian | 0.000 | 1044.000 | 1.000 |
| Teens | sexuality_lesbian | 0.000 | 1044.000 | 1.000 |



### Model: `lr_dp`

**Number of significant subgroup gaps by metric (Holm-adj):**


| namespace | metric | n_significant |
|---|---|---|
| age | DP | 12 |
| age | EO | 16 |
| age | FPR | 2 |
| gender | DP | 8 |
| gender | EO | 2 |
| gender | FPR | 0 |
| hair_color | DP | 12 |
| hair_color | EO | 10 |
| hair_color | FPR | 1 |
| nationality | DP | 31 |
| nationality | EO | 9 |
| nationality | FPR | 0 |
| race_ethnicity | DP | 38 |
| race_ethnicity | EO | 22 |
| race_ethnicity | FPR | 8 |
| sexuality | DP | 0 |
| sexuality | EO | 0 |
| sexuality | FPR | 0 |


#### age

**Top 10 by Δ Demographic Parity:**


| class | subgroup | dp_diff | n_sub | p_dp_adj |
|---|---|---|---|---|
| Big Tits | age_young | -0.220 | 1507.000 | 0.000 |
| Big Tits | age_mature | 0.112 | 2954.000 | 0.000 |
| Teens | age_young | 0.112 | 1507.000 | 0.000 |
| Blonde | age_young | -0.099 | 1507.000 | 0.000 |
| Teens | age_mature | -0.057 | 2954.000 | 0.000 |
| Blonde | age_mature | 0.051 | 2954.000 | 0.000 |
| Blowjob | age_young | -0.042 | 1507.000 | 0.000 |
| Masturbation | age_young | -0.036 | 1507.000 | 0.000 |
| Group | age_young | -0.033 | 1507.000 | 0.000 |
| Blowjob | age_mature | 0.021 | 2954.000 | 0.000 |

**Top 10 by Δ Equal Opportunity:**


| class | subgroup | eo_diff | n_sub | p_eo_adj |
|---|---|---|---|---|
| Teens | age_mature | 0.218 | 2954.000 | 0.000 |
| Group | age_young | -0.132 | 1507.000 | 0.014 |
| Blonde | age_young | -0.126 | 1507.000 | 0.000 |
| Cumshot | age_young | -0.114 | 1507.000 | 0.000 |
| Amateur | age_young | -0.113 | 1507.000 | 0.000 |
| Amateur | age_mature | 0.080 | 2954.000 | 0.000 |
| Teens | age_young | -0.074 | 1507.000 | 0.000 |
| Cumshot | age_mature | 0.074 | 2954.000 | 0.000 |
| Big Tits | age_young | -0.068 | 1507.000 | 0.002 |
| Lesbian | age_young | 0.043 | 1507.000 | 0.091 |

**Top 10 by Δ False Positive Rate:**


| class | subgroup | fpr_diff | n_sub | p_fpr_adj |
|---|---|---|---|---|
| Masturbation | age_young | 0.004 | 1507.000 | 0.047 |
| Big Tits | age_mature | -0.003 | 2954.000 | 0.113 |
| Big Tits | age_young | 0.003 | 1507.000 | 0.113 |
| Amateur | age_young | 0.003 | 1507.000 | 0.714 |
| Fetish | age_young | 0.002 | 1507.000 | 0.295 |
| Masturbation | age_mature | -0.002 | 2954.000 | 0.047 |
| Fetish | age_mature | -0.001 | 2954.000 | 0.295 |
| Amateur | age_mature | -0.001 | 2954.000 | 0.714 |
| Anal | age_young | 0.001 | 1507.000 | 0.432 |
| Blowjob | age_young | -0.001 | 1507.000 | 0.580 |


#### gender

**Top 10 by Δ Demographic Parity:**


| class | subgroup | dp_diff | n_sub | p_dp_adj |
|---|---|---|---|---|
| Blowjob | gender_male | 0.321 | 185.000 | 0.000 |
| Masturbation | gender_male | -0.204 | 185.000 | 0.000 |
| Cumshot | gender_male | 0.057 | 185.000 | 0.000 |
| Group | gender_male | 0.048 | 185.000 | 0.000 |
| Teens | gender_male | 0.045 | 185.000 | 0.076 |
| Blonde | gender_male | 0.030 | 185.000 | 0.481 |
| Blowjob | gender_female | -0.026 | 2274.000 | 0.000 |
| Amateur | gender_male | -0.026 | 185.000 | 0.769 |
| Big Tits | gender_male | -0.026 | 185.000 | 0.821 |
| Masturbation | gender_female | 0.017 | 2274.000 | 0.000 |

**Top 10 by Δ Equal Opportunity:**


| class | subgroup | eo_diff | n_sub | p_eo_adj |
|---|---|---|---|---|
| Cumshot | gender_male | -0.177 | 185.000 | 0.023 |
| Anal | gender_male | 0.118 | 185.000 | 0.612 |
| Masturbation | gender_male | 0.099 | 185.000 | 0.186 |
| Fetish | gender_male | 0.093 | 185.000 | 0.706 |
| Cumshot | gender_female | 0.055 | 2274.000 | 0.023 |
| Interracial | gender_male | -0.051 | 185.000 | 0.633 |
| Big Tits | gender_male | -0.045 | 185.000 | 0.762 |
| Amateur | gender_male | 0.042 | 185.000 | 0.930 |
| Blowjob | gender_male | 0.040 | 185.000 | 0.577 |
| Asian | gender_male | 0.035 | 185.000 | 0.798 |

**Top 10 by Δ False Positive Rate:**


| class | subgroup | fpr_diff | n_sub | p_fpr_adj |
|---|---|---|---|---|
| Cumshot | gender_male | 0.005 | 185.000 | 0.125 |
| Big Tits | gender_male | -0.005 | 185.000 | 0.830 |
| Fetish | gender_male | 0.002 | 185.000 | 1.000 |
| Anal | gender_male | -0.002 | 185.000 | 1.000 |
| Teens | gender_male | -0.001 | 185.000 | 1.000 |
| Amateur | gender_male | -0.001 | 185.000 | 1.000 |
| Asian | gender_male | -0.000 | 185.000 | 1.000 |
| Big Tits | gender_female | 0.000 | 2274.000 | 0.830 |
| Cumshot | gender_female | -0.000 | 2274.000 | 0.125 |
| Anal | gender_female | -0.000 | 2274.000 | 1.000 |


#### hair_color

**Top 10 by Δ Demographic Parity:**


| class | subgroup | dp_diff | n_sub | p_dp_adj |
|---|---|---|---|---|
| Blonde | blonde | 0.345 | 3954.000 | 0.000 |
| Blonde | brunette | -0.200 | 6045.000 | 0.000 |
| Blonde | redhead | -0.188 | 821.000 | 0.000 |
| Blowjob | redhead | -0.113 | 821.000 | 0.000 |
| Amateur | redhead | 0.052 | 821.000 | 0.000 |
| Big Tits | blonde | 0.046 | 3954.000 | 0.000 |
| Teens | redhead | -0.031 | 821.000 | 0.052 |
| Big Tits | brunette | -0.031 | 6045.000 | 0.000 |
| Masturbation | redhead | -0.025 | 821.000 | 0.226 |
| Blowjob | blonde | 0.016 | 3954.000 | 0.021 |

**Top 10 by Δ Equal Opportunity:**


| class | subgroup | eo_diff | n_sub | p_eo_adj |
|---|---|---|---|---|
| Blonde | brunette | -0.248 | 6045.000 | 0.000 |
| Blonde | redhead | -0.214 | 821.000 | 0.000 |
| Masturbation | redhead | -0.119 | 821.000 | 0.000 |
| Big Tits | redhead | -0.111 | 821.000 | 0.000 |
| Blowjob | redhead | -0.101 | 821.000 | 0.000 |
| Anal | redhead | -0.078 | 821.000 | 0.055 |
| Asian | redhead | 0.068 | 821.000 | 0.669 |
| Group | redhead | -0.062 | 821.000 | 0.440 |
| Blonde | blonde | 0.057 | 3954.000 | 0.000 |
| Teens | redhead | -0.046 | 821.000 | 0.179 |

**Top 10 by Δ False Positive Rate:**


| class | subgroup | fpr_diff | n_sub | p_fpr_adj |
|---|---|---|---|---|
| Amateur | redhead | 0.004 | 821.000 | 0.466 |
| Blowjob | redhead | 0.002 | 821.000 | 0.004 |
| Teens | redhead | 0.002 | 821.000 | 0.061 |
| Big Tits | blonde | -0.001 | 3954.000 | 0.840 |
| Amateur | blonde | -0.001 | 3954.000 | 1.000 |
| Masturbation | redhead | -0.001 | 821.000 | 1.000 |
| Anal | redhead | -0.001 | 821.000 | 0.629 |
| Fetish | blonde | -0.001 | 3954.000 | 0.918 |
| Big Tits | brunette | 0.001 | 6045.000 | 0.840 |
| Big Tits | redhead | -0.000 | 821.000 | 0.855 |


#### nationality

**Top 10 by Δ Demographic Parity:**


| class | subgroup | dp_diff | n_sub | p_dp_adj |
|---|---|---|---|---|
| Blowjob | south_asian | -0.313 | 128.000 | 0.000 |
| Big Tits | south_asian | -0.155 | 128.000 | 0.000 |
| Masturbation | south_asian | -0.131 | 128.000 | 0.001 |
| Blonde | africa | 0.130 | 380.000 | 0.000 |
| Blonde | east_asian | -0.115 | 886.000 | 0.000 |
| Masturbation | east_asian | 0.097 | 886.000 | 0.000 |
| Blonde | south_asian | -0.094 | 128.000 | 0.000 |
| Big Tits | east_asian | -0.085 | 886.000 | 0.000 |
| Amateur | east_asian | -0.081 | 886.000 | 0.000 |
| Teens | south_asian | -0.077 | 128.000 | 0.034 |

**Top 10 by Δ Equal Opportunity:**


| class | subgroup | eo_diff | n_sub | p_eo_adj |
|---|---|---|---|---|
| Cumshot | south_asian | -0.218 | 128.000 | 0.003 |
| Anal | south_asian | 0.204 | 128.000 | 0.678 |
| Blonde | east_asian | -0.200 | 886.000 | 0.991 |
| Fetish | east_asian | 0.190 | 886.000 | 0.141 |
| Amateur | africa | 0.154 | 380.000 | 0.005 |
| Masturbation | east_asian | 0.141 | 886.000 | 0.000 |
| Teens | east_asian | 0.126 | 886.000 | 0.001 |
| Big Tits | east_asian | 0.120 | 886.000 | 0.000 |
| Lesbian | east_asian | 0.109 | 886.000 | 0.107 |
| Asian | africa | -0.105 | 380.000 | 1.000 |

**Top 10 by Δ False Positive Rate:**


| class | subgroup | fpr_diff | n_sub | p_fpr_adj |
|---|---|---|---|---|
| Amateur | south_asian | -0.005 | 128.000 | 1.000 |
| Masturbation | south_asian | -0.003 | 128.000 | 1.000 |
| Fetish | africa | 0.002 | 380.000 | 0.057 |
| Group | east_asian | 0.002 | 886.000 | 0.141 |
| Cumshot | africa | 0.002 | 380.000 | 1.000 |
| Masturbation | africa | 0.001 | 380.000 | 1.000 |
| Cumshot | south_asian | -0.001 | 128.000 | 1.000 |
| Amateur | africa | 0.001 | 380.000 | 1.000 |
| Big Tits | europe | 0.001 | 1242.000 | 0.927 |
| Masturbation | east_asian | -0.001 | 886.000 | 1.000 |


#### race_ethnicity

**Top 10 by Δ Demographic Parity:**


| class | subgroup | dp_diff | n_sub | p_dp_adj |
|---|---|---|---|---|
| Blonde | asian | -0.194 | 1173.000 | 0.000 |
| Blonde | latina | -0.170 | 836.000 | 0.000 |
| Masturbation | mixed_or_other | -0.157 | 1167.000 | 0.000 |
| Big Tits | asian | -0.129 | 1173.000 | 0.000 |
| Blonde | black | -0.099 | 2300.000 | 0.000 |
| Asian | asian | 0.087 | 1173.000 | 0.000 |
| Blonde | white | 0.085 | 6901.000 | 0.000 |
| Masturbation | latina | -0.084 | 836.000 | 0.000 |
| Interracial | mixed_or_other | 0.055 | 1167.000 | 0.000 |
| Big Tits | latina | 0.052 | 836.000 | 0.003 |

**Top 10 by Δ Equal Opportunity:**


| class | subgroup | eo_diff | n_sub | p_eo_adj |
|---|---|---|---|---|
| Blonde | latina | -0.376 | 836.000 | 0.000 |
| Blonde | asian | -0.311 | 1173.000 | 0.000 |
| Teens | latina | -0.232 | 836.000 | 0.000 |
| Group | latina | -0.106 | 836.000 | 0.286 |
| Group | mixed_or_other | -0.100 | 1167.000 | 0.017 |
| Blowjob | mixed_or_other | -0.100 | 1167.000 | 0.000 |
| Lesbian | latina | -0.093 | 836.000 | 0.081 |
| Fetish | asian | 0.092 | 1173.000 | 0.371 |
| Big Tits | asian | 0.091 | 1173.000 | 0.000 |
| Cumshot | latina | -0.090 | 836.000 | 0.000 |

**Top 10 by Δ False Positive Rate:**


| class | subgroup | fpr_diff | n_sub | p_fpr_adj |
|---|---|---|---|---|
| Asian | asian | 0.053 | 1173.000 | 0.000 |
| Amateur | latina | 0.007 | 836.000 | 0.002 |
| Teens | latina | 0.004 | 836.000 | 0.000 |
| Amateur | black | 0.004 | 2300.000 | 0.001 |
| Amateur | mixed_or_other | -0.003 | 1167.000 | 0.108 |
| Fetish | latina | 0.003 | 836.000 | 0.066 |
| Cumshot | latina | 0.003 | 836.000 | 0.002 |
| Masturbation | latina | 0.003 | 836.000 | 0.198 |
| Amateur | white | -0.002 | 6901.000 | 0.001 |
| Big Tits | latina | 0.002 | 836.000 | 0.169 |


#### sexuality

**Top 10 by Δ Demographic Parity:**


| class | subgroup | dp_diff | n_sub | p_dp_adj |
|---|---|---|---|---|
| Blowjob | sexuality_lesbian | -0.026 | 1044.000 | 1.000 |
| Masturbation | sexuality_lesbian | 0.014 | 1044.000 | 1.000 |
| Cumshot | sexuality_lesbian | -0.014 | 1044.000 | 1.000 |
| Anal | sexuality_lesbian | -0.010 | 1044.000 | 1.000 |
| Big Tits | sexuality_lesbian | 0.006 | 1044.000 | 1.000 |
| Teens | sexuality_lesbian | 0.004 | 1044.000 | 1.000 |
| Lesbian | sexuality_lesbian | 0.002 | 1044.000 | 1.000 |
| Fetish | sexuality_lesbian | -0.002 | 1044.000 | 1.000 |
| Group | sexuality_lesbian | -0.002 | 1044.000 | 1.000 |
| Amateur | sexuality_lesbian | -0.002 | 1044.000 | 1.000 |

**Top 10 by Δ Equal Opportunity:**


| class | subgroup | eo_diff | n_sub | p_eo_adj |
|---|---|---|---|---|
| Cumshot | sexuality_lesbian | -0.682 | 1044.000 | 1.000 |
| Blowjob | sexuality_lesbian | -0.166 | 1044.000 | 1.000 |
| Group | sexuality_lesbian | 0.073 | 1044.000 | 1.000 |
| Anal | sexuality_lesbian | 0.021 | 1044.000 | 1.000 |
| Teens | sexuality_lesbian | 0.011 | 1044.000 | 1.000 |
| Amateur | sexuality_lesbian | 0.010 | 1044.000 | 1.000 |
| Fetish | sexuality_lesbian | -0.006 | 1044.000 | 1.000 |
| Blonde | sexuality_lesbian | -0.004 | 1044.000 | 1.000 |
| Masturbation | sexuality_lesbian | 0.003 | 1044.000 | 1.000 |
| Big Tits | sexuality_lesbian | 0.002 | 1044.000 | 1.000 |

**Top 10 by Δ False Positive Rate:**


| class | subgroup | fpr_diff | n_sub | p_fpr_adj |
|---|---|---|---|---|
| Anal | sexuality_lesbian | -0.001 | 1044.000 | 1.000 |
| Blowjob | sexuality_lesbian | 0.000 | 1044.000 | 1.000 |
| Masturbation | sexuality_lesbian | 0.000 | 1044.000 | 1.000 |
| Big Tits | sexuality_lesbian | 0.000 | 1044.000 | 1.000 |
| Blonde | sexuality_lesbian | 0.000 | 1044.000 | 1.000 |
| Teens | sexuality_lesbian | 0.000 | 1044.000 | 1.000 |
| Amateur | sexuality_lesbian | 0.000 | 1044.000 | 1.000 |
| Group | sexuality_lesbian | 0.000 | 1044.000 | 1.000 |
| Cumshot | sexuality_lesbian | 0.000 | 1044.000 | 1.000 |
| Asian | sexuality_lesbian | 0.000 | 1044.000 | 1.000 |



### Model: `rf`

**Number of significant subgroup gaps by metric (Holm-adj):**


| namespace | metric | n_significant |
|---|---|---|
| age | DP | 20 |
| age | EO | 10 |
| age | FPR | 8 |
| gender | DP | 18 |
| gender | EO | 2 |
| gender | FPR | 10 |
| hair_color | DP | 21 |
| hair_color | EO | 17 |
| hair_color | FPR | 7 |
| nationality | DP | 37 |
| nationality | EO | 21 |
| nationality | FPR | 14 |
| race_ethnicity | DP | 47 |
| race_ethnicity | EO | 37 |
| race_ethnicity | FPR | 24 |
| sexuality | DP | 0 |
| sexuality | EO | 0 |
| sexuality | FPR | 0 |


#### age

**Top 10 by Δ Demographic Parity:**


| class | subgroup | dp_diff | n_sub | p_dp_adj |
|---|---|---|---|---|
| Big Tits | age_young | -0.302 | 1507.000 | 0.000 |
| Teens | age_young | 0.266 | 1507.000 | 0.000 |
| Big Tits | age_mature | 0.154 | 2954.000 | 0.000 |
| Teens | age_mature | -0.136 | 2954.000 | 0.000 |
| Blonde | age_young | -0.112 | 1507.000 | 0.000 |
| Amateur | age_young | 0.104 | 1507.000 | 0.000 |
| Masturbation | age_young | -0.058 | 1507.000 | 0.000 |
| Blonde | age_mature | 0.057 | 2954.000 | 0.000 |
| Amateur | age_mature | -0.053 | 2954.000 | 0.000 |
| Lesbian | age_young | -0.037 | 1507.000 | 0.000 |

**Top 10 by Δ Equal Opportunity:**


| class | subgroup | eo_diff | n_sub | p_eo_adj |
|---|---|---|---|---|
| Teens | age_mature | -0.182 | 2954.000 | 0.000 |
| Amateur | age_young | 0.156 | 1507.000 | 0.000 |
| Big Tits | age_young | -0.139 | 1507.000 | 0.000 |
| Amateur | age_mature | -0.110 | 2954.000 | 0.000 |
| Fetish | age_young | -0.085 | 1507.000 | 0.072 |
| Blonde | age_young | -0.072 | 1507.000 | 0.000 |
| Teens | age_young | 0.062 | 1507.000 | 0.000 |
| Masturbation | age_young | -0.060 | 1507.000 | 0.000 |
| Interracial | age_young | 0.056 | 1507.000 | 0.449 |
| Fetish | age_mature | 0.049 | 2954.000 | 0.072 |

**Top 10 by Δ False Positive Rate:**


| class | subgroup | fpr_diff | n_sub | p_fpr_adj |
|---|---|---|---|---|
| Big Tits | age_mature | 0.037 | 2954.000 | 0.000 |
| Big Tits | age_young | -0.032 | 1507.000 | 0.000 |
| Teens | age_young | 0.030 | 1507.000 | 0.000 |
| Masturbation | age_young | -0.016 | 1507.000 | 0.151 |
| Amateur | age_young | 0.014 | 1507.000 | 0.000 |
| Masturbation | age_mature | 0.009 | 2954.000 | 0.151 |
| Teens | age_mature | -0.009 | 2954.000 | 0.000 |
| Blowjob | age_young | -0.008 | 1507.000 | 0.809 |
| Group | age_young | -0.007 | 1507.000 | 0.018 |
| Amateur | age_mature | -0.006 | 2954.000 | 0.000 |


#### gender

**Top 10 by Δ Demographic Parity:**


| class | subgroup | dp_diff | n_sub | p_dp_adj |
|---|---|---|---|---|
| Blowjob | gender_male | 0.415 | 185.000 | 0.000 |
| Masturbation | gender_male | -0.283 | 185.000 | 0.000 |
| Teens | gender_male | 0.091 | 185.000 | 0.001 |
| Big Tits | gender_male | -0.077 | 185.000 | 0.045 |
| Group | gender_male | 0.073 | 185.000 | 0.000 |
| Asian | gender_male | 0.070 | 185.000 | 0.001 |
| Cumshot | gender_male | 0.066 | 185.000 | 0.000 |
| Blonde | gender_male | 0.056 | 185.000 | 0.134 |
| Lesbian | gender_male | -0.034 | 185.000 | 0.016 |
| Blowjob | gender_female | -0.034 | 2274.000 | 0.000 |

**Top 10 by Δ Equal Opportunity:**


| class | subgroup | eo_diff | n_sub | p_eo_adj |
|---|---|---|---|---|
| Amateur | gender_male | 0.120 | 185.000 | 0.177 |
| Big Tits | gender_male | -0.115 | 185.000 | 0.002 |
| Asian | gender_male | 0.108 | 185.000 | 0.141 |
| Anal | gender_male | -0.089 | 185.000 | 0.169 |
| Group | gender_male | 0.073 | 185.000 | 0.812 |
| Blowjob | gender_male | 0.058 | 185.000 | 0.138 |
| Fetish | gender_male | 0.055 | 185.000 | 1.000 |
| Blonde | gender_male | 0.048 | 185.000 | 0.441 |
| Cumshot | gender_male | -0.041 | 185.000 | 1.000 |
| Interracial | gender_male | 0.038 | 185.000 | 1.000 |

**Top 10 by Δ False Positive Rate:**


| class | subgroup | fpr_diff | n_sub | p_fpr_adj |
|---|---|---|---|---|
| Blowjob | gender_male | 0.141 | 185.000 | 0.000 |
| Big Tits | gender_male | -0.044 | 185.000 | 0.049 |
| Teens | gender_male | 0.023 | 185.000 | 0.000 |
| Masturbation | gender_male | -0.014 | 185.000 | 1.000 |
| Group | gender_male | 0.014 | 185.000 | 0.008 |
| Cumshot | gender_male | 0.011 | 185.000 | 0.001 |
| Anal | gender_male | -0.009 | 185.000 | 0.423 |
| Blonde | gender_male | -0.007 | 185.000 | 0.642 |
| Blowjob | gender_female | -0.005 | 2274.000 | 0.000 |
| Big Tits | gender_female | 0.004 | 2274.000 | 0.049 |


#### hair_color

**Top 10 by Δ Demographic Parity:**


| class | subgroup | dp_diff | n_sub | p_dp_adj |
|---|---|---|---|---|
| Blonde | blonde | 0.478 | 3954.000 | 0.000 |
| Blonde | brunette | -0.280 | 6045.000 | 0.000 |
| Blonde | redhead | -0.243 | 821.000 | 0.000 |
| Blowjob | redhead | -0.075 | 821.000 | 0.000 |
| Asian | blonde | -0.070 | 3954.000 | 0.000 |
| Big Tits | blonde | 0.054 | 3954.000 | 0.000 |
| Asian | brunette | 0.053 | 6045.000 | 0.000 |
| Asian | redhead | -0.051 | 821.000 | 0.000 |
| Big Tits | redhead | 0.047 | 821.000 | 0.004 |
| Amateur | redhead | 0.046 | 821.000 | 0.000 |

**Top 10 by Δ Equal Opportunity:**


| class | subgroup | eo_diff | n_sub | p_eo_adj |
|---|---|---|---|---|
| Asian | blonde | -0.584 | 3954.000 | 0.000 |
| Asian | redhead | -0.183 | 821.000 | 0.012 |
| Blonde | brunette | -0.151 | 6045.000 | 0.000 |
| Interracial | redhead | -0.111 | 821.000 | 0.128 |
| Cumshot | blonde | -0.058 | 3954.000 | 0.003 |
| Cumshot | brunette | 0.045 | 6045.000 | 0.003 |
| Asian | brunette | 0.038 | 6045.000 | 0.000 |
| Blowjob | redhead | -0.038 | 821.000 | 0.002 |
| Fetish | redhead | -0.038 | 821.000 | 1.000 |
| Anal | redhead | -0.035 | 821.000 | 0.316 |

**Top 10 by Δ False Positive Rate:**


| class | subgroup | fpr_diff | n_sub | p_fpr_adj |
|---|---|---|---|---|
| Blonde | blonde | 0.383 | 3954.000 | 0.000 |
| Masturbation | blonde | -0.036 | 3954.000 | 0.000 |
| Masturbation | brunette | 0.025 | 6045.000 | 0.000 |
| Masturbation | redhead | -0.014 | 821.000 | 0.438 |
| Big Tits | blonde | 0.009 | 3954.000 | 0.011 |
| Group | redhead | -0.009 | 821.000 | 0.178 |
| Amateur | redhead | 0.007 | 821.000 | 0.040 |
| Blowjob | redhead | 0.007 | 821.000 | 1.000 |
| Fetish | redhead | 0.007 | 821.000 | 0.137 |
| Blonde | brunette | -0.005 | 6045.000 | 0.000 |


#### nationality

**Top 10 by Δ Demographic Parity:**


| class | subgroup | dp_diff | n_sub | p_dp_adj |
|---|---|---|---|---|
| Asian | east_asian | 0.661 | 886.000 | 0.000 |
| Blowjob | south_asian | -0.403 | 128.000 | 0.000 |
| Masturbation | south_asian | -0.302 | 128.000 | 0.000 |
| Asian | south_asian | -0.297 | 128.000 | 0.000 |
| Asian | europe | -0.295 | 1242.000 | 0.000 |
| Asian | africa | -0.281 | 380.000 | 0.000 |
| Blonde | east_asian | -0.204 | 886.000 | 0.000 |
| Big Tits | south_asian | -0.199 | 128.000 | 0.000 |
| Masturbation | east_asian | 0.176 | 886.000 | 0.000 |
| Blonde | africa | 0.174 | 380.000 | 0.000 |

**Top 10 by Δ Equal Opportunity:**


| class | subgroup | eo_diff | n_sub | p_eo_adj |
|---|---|---|---|---|
| Asian | south_asian | -0.935 | 128.000 | 0.000 |
| Asian | europe | -0.781 | 1242.000 | 0.000 |
| Amateur | south_asian | -0.478 | 128.000 | 0.000 |
| Blonde | east_asian | -0.402 | 886.000 | 0.011 |
| Interracial | south_asian | -0.379 | 128.000 | 0.202 |
| Interracial | east_asian | -0.355 | 886.000 | 0.278 |
| Asian | africa | -0.335 | 380.000 | 0.000 |
| Teens | south_asian | -0.287 | 128.000 | 0.004 |
| Cumshot | africa | -0.247 | 380.000 | 0.018 |
| Cumshot | south_asian | -0.226 | 128.000 | 0.452 |

**Top 10 by Δ False Positive Rate:**


| class | subgroup | fpr_diff | n_sub | p_fpr_adj |
|---|---|---|---|---|
| Masturbation | east_asian | 0.217 | 886.000 | 0.000 |
| Asian | east_asian | 0.198 | 886.000 | 0.000 |
| Masturbation | south_asian | -0.197 | 128.000 | 0.000 |
| Masturbation | africa | -0.112 | 380.000 | 0.000 |
| Blowjob | south_asian | -0.102 | 128.000 | 0.001 |
| Masturbation | europe | -0.058 | 1242.000 | 0.000 |
| Blowjob | europe | 0.041 | 1242.000 | 0.000 |
| Group | south_asian | -0.029 | 128.000 | 0.109 |
| Blowjob | east_asian | -0.028 | 886.000 | 0.146 |
| Blowjob | africa | -0.027 | 380.000 | 0.299 |


#### race_ethnicity

**Top 10 by Δ Demographic Parity:**


| class | subgroup | dp_diff | n_sub | p_dp_adj |
|---|---|---|---|---|
| Asian | asian | 0.709 | 1173.000 | 0.000 |
| Interracial | mixed_or_other | 0.454 | 1167.000 | 0.000 |
| Blonde | asian | -0.251 | 1173.000 | 0.000 |
| Masturbation | mixed_or_other | -0.241 | 1167.000 | 0.000 |
| Blonde | latina | -0.235 | 836.000 | 0.000 |
| Big Tits | asian | -0.205 | 1173.000 | 0.000 |
| Blonde | black | -0.140 | 2300.000 | 0.000 |
| Blowjob | mixed_or_other | 0.140 | 1167.000 | 0.000 |
| Interracial | asian | -0.128 | 1173.000 | 0.000 |
| Blonde | white | 0.116 | 6901.000 | 0.000 |

**Top 10 by Δ Equal Opportunity:**


| class | subgroup | eo_diff | n_sub | p_eo_adj |
|---|---|---|---|---|
| Asian | latina | -0.723 | 836.000 | 0.000 |
| Asian | white | -0.611 | 6901.000 | 0.000 |
| Blonde | latina | -0.560 | 836.000 | 0.000 |
| Asian | mixed_or_other | -0.556 | 1167.000 | 0.000 |
| Fetish | latina | -0.285 | 836.000 | 0.008 |
| Group | latina | -0.271 | 836.000 | 0.000 |
| Blonde | asian | -0.261 | 1173.000 | 0.000 |
| Fetish | asian | 0.257 | 1173.000 | 0.026 |
| Fetish | mixed_or_other | -0.256 | 1167.000 | 0.000 |
| Teens | mixed_or_other | -0.244 | 1167.000 | 0.000 |

**Top 10 by Δ False Positive Rate:**


| class | subgroup | fpr_diff | n_sub | p_fpr_adj |
|---|---|---|---|---|
| Masturbation | asian | 0.197 | 1173.000 | 0.000 |
| Asian | asian | 0.158 | 1173.000 | 0.000 |
| Masturbation | mixed_or_other | -0.111 | 1167.000 | 0.000 |
| Blowjob | mixed_or_other | 0.109 | 1167.000 | 0.000 |
| Masturbation | black | -0.060 | 2300.000 | 0.000 |
| Blowjob | asian | -0.045 | 1173.000 | 0.016 |
| Big Tits | asian | -0.029 | 1173.000 | 0.000 |
| Interracial | mixed_or_other | 0.028 | 1167.000 | 0.000 |
| Big Tits | latina | 0.028 | 836.000 | 0.004 |
| Group | mixed_or_other | 0.023 | 1167.000 | 0.000 |


#### sexuality

**Top 10 by Δ Demographic Parity:**


| class | subgroup | dp_diff | n_sub | p_dp_adj |
|---|---|---|---|---|
| Lesbian | sexuality_lesbian | 0.043 | 1044.000 | 1.000 |
| Blowjob | sexuality_lesbian | -0.035 | 1044.000 | 1.000 |
| Masturbation | sexuality_lesbian | 0.034 | 1044.000 | 1.000 |
| Anal | sexuality_lesbian | -0.016 | 1044.000 | 1.000 |
| Cumshot | sexuality_lesbian | -0.012 | 1044.000 | 1.000 |
| Big Tits | sexuality_lesbian | 0.007 | 1044.000 | 1.000 |
| Group | sexuality_lesbian | -0.005 | 1044.000 | 1.000 |
| Fetish | sexuality_lesbian | 0.004 | 1044.000 | 1.000 |
| Blonde | sexuality_lesbian | 0.004 | 1044.000 | 1.000 |
| Teens | sexuality_lesbian | 0.004 | 1044.000 | 1.000 |

**Top 10 by Δ Equal Opportunity:**


| class | subgroup | eo_diff | n_sub | p_eo_adj |
|---|---|---|---|---|
| Cumshot | sexuality_lesbian | -0.591 | 1044.000 | 1.000 |
| Blowjob | sexuality_lesbian | -0.227 | 1044.000 | 1.000 |
| Fetish | sexuality_lesbian | 0.043 | 1044.000 | 1.000 |
| Amateur | sexuality_lesbian | 0.019 | 1044.000 | 1.000 |
| Asian | sexuality_lesbian | 0.014 | 1044.000 | 1.000 |
| Teens | sexuality_lesbian | 0.010 | 1044.000 | 1.000 |
| Masturbation | sexuality_lesbian | 0.009 | 1044.000 | 1.000 |
| Group | sexuality_lesbian | 0.004 | 1044.000 | 1.000 |
| Anal | sexuality_lesbian | 0.004 | 1044.000 | 1.000 |
| Blonde | sexuality_lesbian | 0.002 | 1044.000 | 1.000 |

**Top 10 by Δ False Positive Rate:**


| class | subgroup | fpr_diff | n_sub | p_fpr_adj |
|---|---|---|---|---|
| Lesbian | sexuality_lesbian | 0.101 | 1044.000 | 1.000 |
| Masturbation | sexuality_lesbian | 0.066 | 1044.000 | 1.000 |
| Blowjob | sexuality_lesbian | -0.002 | 1044.000 | 1.000 |
| Big Tits | sexuality_lesbian | 0.001 | 1044.000 | 1.000 |
| Amateur | sexuality_lesbian | -0.001 | 1044.000 | 1.000 |
| Group | sexuality_lesbian | -0.001 | 1044.000 | 1.000 |
| Fetish | sexuality_lesbian | 0.001 | 1044.000 | 1.000 |
| Anal | sexuality_lesbian | -0.001 | 1044.000 | 1.000 |
| Blonde | sexuality_lesbian | -0.000 | 1044.000 | 1.000 |
| Teens | sexuality_lesbian | 0.000 | 1044.000 | 1.000 |




---

## Intersections Overview

### Model: `lr`

| combo | DP_sig | EO_sig | FPR_sig |
|---|---|---|---|
| age*gender*hair_color | 17 | 1 | 1 |
| age*gender*race_ethnicity | 8 | 0 | 0 |
| age*gender | 18 | 4 | 2 |
| age*hair_color*nationality | 4 | 0 | 2 |
| age*hair_color*race_ethnicity | 53 | 8 | 6 |
| age*hair_color*sexuality | 4 | 0 | 2 |
| age*hair_color | 33 | 7 | 4 |
| age*nationality*race_ethnicity | 6 | 0 | 0 |
| age*nationality | 19 | 1 | 0 |
| age*race_ethnicity*sexuality | 0 | 0 | 0 |
| age*race_ethnicity | 51 | 10 | 10 |
| age*sexuality | 0 | 0 | 0 |
| dp_age*gender*hair_color | 10 | 6 | 0 |
| dp_age*gender*race_ethnicity | 10 | 2 | 0 |
| dp_age*gender | 16 | 8 | 0 |
| dp_age*hair_color*nationality | 2 | 2 | 0 |
| dp_age*hair_color*race_ethnicity | 30 | 12 | 5 |
| dp_age*hair_color*sexuality | 2 | 0 | 0 |
| dp_age*hair_color | 22 | 16 | 1 |
| dp_age*nationality*race_ethnicity | 8 | 2 | 0 |
| dp_age*nationality | 12 | 5 | 0 |
| dp_age*race_ethnicity*sexuality | 0 | 0 | 0 |
| dp_age*race_ethnicity | 35 | 20 | 7 |
| dp_age*sexuality | 0 | 0 | 0 |
| dp_gender*hair_color*nationality | 8 | 4 | 0 |
| dp_gender*hair_color*race_ethnicity | 20 | 6 | 2 |
| dp_gender*hair_color | 9 | 4 | 0 |
| dp_gender*nationality*race_ethnicity | 10 | 2 | 0 |
| dp_gender*nationality | 10 | 6 | 0 |
| dp_gender*race_ethnicity | 26 | 18 | 4 |
| dp_hair_color*nationality*race_ethnicity | 31 | 15 | 0 |
| dp_hair_color*nationality | 35 | 15 | 2 |
| dp_hair_color*race_ethnicity*sexuality | 5 | 5 | 0 |
| dp_hair_color*race_ethnicity | 51 | 30 | 4 |
| dp_hair_color*sexuality | 3 | 4 | 0 |
| dp_nationality*race_ethnicity*sexuality | 0 | 0 | 0 |
| dp_nationality*race_ethnicity | 30 | 6 | 0 |
| dp_nationality*sexuality | 0 | 0 | 0 |
| dp_race_ethnicity*sexuality | 2 | 2 | 0 |
| eo_age*gender*hair_color | 17 | 2 | 1 |
| eo_age*gender*race_ethnicity | 8 | 0 | 0 |
| eo_age*gender | 18 | 6 | 2 |
| eo_age*hair_color*nationality | 4 | 0 | 0 |
| eo_age*hair_color*race_ethnicity | 55 | 7 | 7 |
| eo_age*hair_color*sexuality | 4 | 0 | 0 |
| eo_age*hair_color | 35 | 8 | 5 |
| eo_age*nationality*race_ethnicity | 6 | 0 | 0 |
| eo_age*nationality | 18 | 1 | 0 |
| eo_age*race_ethnicity*sexuality | 0 | 0 | 0 |
| eo_age*race_ethnicity | 52 | 12 | 7 |
| eo_age*sexuality | 0 | 0 | 0 |
| eo_gender*hair_color*nationality | 12 | 0 | 0 |
| eo_gender*hair_color*race_ethnicity | 26 | 7 | 5 |
| eo_gender*hair_color | 13 | 5 | 2 |
| eo_gender*nationality*race_ethnicity | 14 | 4 | 0 |
| eo_gender*nationality | 16 | 2 | 0 |
| eo_gender*race_ethnicity | 31 | 11 | 6 |
| eo_hair_color*nationality*race_ethnicity | 38 | 7 | 2 |
| eo_hair_color*nationality | 40 | 9 | 2 |
| eo_hair_color*race_ethnicity*sexuality | 9 | 0 | 0 |
| eo_hair_color*race_ethnicity | 78 | 24 | 8 |
| eo_hair_color*sexuality | 6 | 0 | 1 |
| eo_nationality*race_ethnicity*sexuality | 0 | 0 | 0 |
| eo_nationality*race_ethnicity | 37 | 6 | 2 |
| eo_nationality*sexuality | 0 | 0 | 0 |
| eo_race_ethnicity*sexuality | 6 | 2 | 0 |
| gender*hair_color*nationality | 12 | 0 | 0 |
| gender*hair_color*race_ethnicity | 25 | 3 | 6 |
| gender*hair_color | 14 | 7 | 2 |
| gender*nationality*race_ethnicity | 14 | 2 | 0 |
| gender*nationality | 16 | 2 | 0 |
| gender*race_ethnicity | 30 | 9 | 8 |
| hair_color*nationality*race_ethnicity | 39 | 6 | 2 |
| hair_color*nationality | 40 | 5 | 5 |
| hair_color*race_ethnicity*sexuality | 8 | 2 | 1 |
| hair_color*race_ethnicity | 77 | 24 | 13 |
| hair_color*sexuality | 6 | 0 | 2 |
| nationality*race_ethnicity*sexuality | 0 | 0 | 0 |
| nationality*race_ethnicity | 36 | 4 | 3 |
| nationality*sexuality | 0 | 0 | 0 |
| race_ethnicity*sexuality | 6 | 2 | 0 |



### Model: `lr_eo`

| combo | DP_sig | EO_sig | FPR_sig |
|---|---|---|---|
| age*gender*hair_color | 17 | 2 | 1 |
| age*gender*race_ethnicity | 8 | 0 | 0 |
| age*gender | 18 | 6 | 2 |
| age*hair_color*nationality | 4 | 0 | 0 |
| age*hair_color*race_ethnicity | 55 | 7 | 7 |
| age*hair_color*sexuality | 4 | 0 | 0 |
| age*hair_color | 35 | 8 | 5 |
| age*nationality*race_ethnicity | 6 | 0 | 0 |
| age*nationality | 18 | 1 | 0 |
| age*race_ethnicity*sexuality | 0 | 0 | 0 |
| age*race_ethnicity | 52 | 12 | 7 |
| age*sexuality | 0 | 0 | 0 |
| gender*hair_color*nationality | 12 | 0 | 0 |
| gender*hair_color*race_ethnicity | 26 | 7 | 5 |
| gender*hair_color | 13 | 5 | 2 |
| gender*nationality*race_ethnicity | 14 | 4 | 0 |
| gender*nationality | 16 | 2 | 0 |
| gender*race_ethnicity | 31 | 11 | 6 |
| hair_color*nationality*race_ethnicity | 38 | 7 | 2 |
| hair_color*nationality | 40 | 9 | 2 |
| hair_color*race_ethnicity*sexuality | 9 | 0 | 0 |
| hair_color*race_ethnicity | 78 | 24 | 8 |
| hair_color*sexuality | 6 | 0 | 1 |
| nationality*race_ethnicity*sexuality | 0 | 0 | 0 |
| nationality*race_ethnicity | 37 | 6 | 2 |
| nationality*sexuality | 0 | 0 | 0 |
| race_ethnicity*sexuality | 6 | 2 | 0 |



### Model: `lr_dp`

| combo | DP_sig | EO_sig | FPR_sig |
|---|---|---|---|
| age*gender*hair_color | 10 | 6 | 0 |
| age*gender*race_ethnicity | 10 | 2 | 0 |
| age*gender | 16 | 8 | 0 |
| age*hair_color*nationality | 2 | 2 | 0 |
| age*hair_color*race_ethnicity | 30 | 12 | 5 |
| age*hair_color*sexuality | 2 | 0 | 0 |
| age*hair_color | 22 | 16 | 1 |
| age*nationality*race_ethnicity | 8 | 2 | 0 |
| age*nationality | 12 | 5 | 0 |
| age*race_ethnicity*sexuality | 0 | 0 | 0 |
| age*race_ethnicity | 35 | 20 | 7 |
| age*sexuality | 0 | 0 | 0 |
| gender*hair_color*nationality | 8 | 4 | 0 |
| gender*hair_color*race_ethnicity | 20 | 6 | 2 |
| gender*hair_color | 9 | 4 | 0 |
| gender*nationality*race_ethnicity | 10 | 2 | 0 |
| gender*nationality | 10 | 6 | 0 |
| gender*race_ethnicity | 26 | 18 | 4 |
| hair_color*nationality*race_ethnicity | 31 | 15 | 0 |
| hair_color*nationality | 35 | 15 | 2 |
| hair_color*race_ethnicity*sexuality | 5 | 5 | 0 |
| hair_color*race_ethnicity | 51 | 30 | 4 |
| hair_color*sexuality | 3 | 4 | 0 |
| nationality*race_ethnicity*sexuality | 0 | 0 | 0 |
| nationality*race_ethnicity | 30 | 6 | 0 |
| nationality*sexuality | 0 | 0 | 0 |
| race_ethnicity*sexuality | 2 | 2 | 0 |



### Model: `rf`

| combo | DP_sig | EO_sig | FPR_sig |
|---|---|---|---|
| age*gender*hair_color | 18 | 5 | 4 |
| age*gender*race_ethnicity | 12 | 6 | 4 |
| age*gender | 18 | 10 | 6 |
| age*hair_color*nationality | 4 | 2 | 2 |
| age*hair_color*race_ethnicity | 59 | 24 | 22 |
| age*hair_color*sexuality | 2 | 0 | 2 |
| age*hair_color | 35 | 22 | 13 |
| age*nationality*race_ethnicity | 6 | 4 | 2 |
| age*nationality | 16 | 2 | 5 |
| age*race_ethnicity*sexuality | 0 | 0 | 0 |
| age*race_ethnicity | 60 | 28 | 20 |
| age*sexuality | 0 | 0 | 0 |
| gender*hair_color*nationality | 16 | 8 | 4 |
| gender*hair_color*race_ethnicity | 25 | 13 | 9 |
| gender*hair_color | 8 | 4 | 7 |
| gender*nationality*race_ethnicity | 16 | 8 | 4 |
| gender*nationality | 16 | 8 | 6 |
| gender*race_ethnicity | 37 | 19 | 8 |
| hair_color*nationality*race_ethnicity | 38 | 14 | 9 |
| hair_color*nationality | 40 | 17 | 10 |
| hair_color*race_ethnicity*sexuality | 7 | 4 | 1 |
| hair_color*race_ethnicity | 82 | 45 | 19 |
| hair_color*sexuality | 7 | 3 | 2 |
| nationality*race_ethnicity*sexuality | 0 | 0 | 0 |
| nationality*race_ethnicity | 40 | 23 | 11 |
| nationality*sexuality | 0 | 0 | 0 |
| race_ethnicity*sexuality | 8 | 8 | 2 |


