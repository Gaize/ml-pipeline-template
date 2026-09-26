# Data attribution

## parkinsons.csv

The Oxford Parkinson's Disease Detection Dataset, from the UCI Machine Learning
Repository. The file is the UCI `parkinsons.data` without changes.

- Source: <https://archive.ics.uci.edu/dataset/174/parkinsons> (DOI 10.24432/C59C74)
- Creator: Max Little, University of Oxford
- License: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
- Citation: Little, M., McSharry, P., Roberts, S., Costello, D., and Moroz, I.
  (2007). Exploiting nonlinear recurrence and fractal scaling properties for
  voice disorder detection. *BioMedical Engineering OnLine*, 6:23.

## Counts

The file contains 195 rows and 32 subjects. 147 rows have the label 1 and 48
rows have the label 0. This is 24 subjects and 8 subjects. No subject has both
labels.

The UCI web page and the `parkinsons.names` file give 197 instances and 31
subjects. The file does not agree with them. Count the file before you quote a
number.

## Why the group column is necessary

Each subject made six or seven recordings. The subject key is not a column. It
is the first part of `name`: `phon_R01_S01_1` gives the subject `phon_R01_S01`.

Rows are therefore not independent. If one subject goes into both the training
set and the test set, the model can identify the speaker instead of the
condition. For this reason `group_col` is `subject`.

The pipeline measures the difference. The ROC AUC is 0.844 with subject groups
and 0.909 without them. The value 0.909 is not a better result. It is the same
model, measured on speakers that it has heard before.

## Sources on this risk

- Chaibub Neto et al. examined this dataset. Under record-wise splits, a
  classifier gets a good score on shuffled labels, because it identifies
  speakers. *npj Digital Medicine* 2:99 (2019).
  <https://www.nature.com/articles/s41746-019-0178-x>
- The first paper on this dataset reported 91.4% accuracy. It validated over
  recordings, not over subjects.
  <https://pmc.ncbi.nlm.nih.gov/articles/PMC3051371/>
- Little et al. also show that subject-wise splits are not correct for all data.
  Match the split to the way you will use the model. *GigaScience* 6(5):gix020
  (2017). <https://academic.oup.com/gigascience/article/6/5/gix020/3073663>

The permutation test in this pipeline does not find this problem. It shuffles
the labels against fixed out-of-fold scores, so nothing fits again. Its null
value stays at 0.5 in both cases.
