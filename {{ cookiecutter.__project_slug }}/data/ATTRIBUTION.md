# Data attribution

## parkinsons.csv

Oxford Parkinson's Disease Detection Dataset, from the UCI Machine Learning
Repository.

- **Source:** https://archive.ics.uci.edu/dataset/174/parkinsons (DOI: 10.24432/C59C74)
- **Creators:** Max Little, University of Oxford
- **License:** [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
- **Citation:** Little, M., McSharry, P., Roberts, S., Costello, D., & Moroz, I.
  (2007). Exploiting nonlinear recurrence and fractal scaling properties for
  voice disorder detection. *BioMedical Engineering OnLine*, 6:23.

The file is the UCI `parkinsons.data` verbatim.

### Counts

Counted from the file in this repository: **195 rows, 32 distinct subjects,
147 rows labelled 1 and 48 labelled 0** (24 subjects and 8 subjects
respectively). No subject appears under both labels.

UCI's own landing page and the bundled `parkinsons.names` state 197 instances
and 31 subjects. The file does not agree with them. The numbers above are what
the file contains; count it yourself before quoting either.

### Why this dataset is here

Each subject contributed six or seven voice recordings, and the subject key is
not a column — it is a prefix of `name` (`phon_R01_S01_1` → `phon_R01_S01`).
A split that treats rows as independent puts five of a subject's six recordings
in the training set, so the model can recognise the speaker instead of the
condition.

Chaibub Neto et al. analysed this dataset and found that under record-wise
splits the permutation null is centred far above chance: a classifier scores
well on *shuffled* labels purely by identifying speakers ([npj Digital Medicine
2:99, 2019](https://www.nature.com/articles/s41746-019-0178-x)). The originating
paper's 91.4% ± 4.4% accuracy was itself validated over recordings rather than
subjects ([Little et al., IEEE TBME
2009](https://pmc.ncbi.nlm.nih.gov/articles/PMC3051371/)).

**So `group_col` is `subject` on this dataset, and there is no second option.**
Multiple rows per subject means grouping by subject; anything else scores a model
on people it has already seen.

Running it ungrouped shows what that is worth: **ROC AUC 0.844 grouped against
0.909 ungrouped**, measured with the shipped pipeline on this data. The 0.909 is
not a better result. It is the same model, graded on an exam containing the
answers, and it would not survive contact with a new speaker.

The pipeline's permutation test will not catch this for you. It shuffles labels
against fixed out-of-fold scores, so its null sits at chance either way
(measured: 0.500 ungrouped, 0.501 grouped). Reproducing the Chaibub Neto result
means permuting the labels and re-running the entire cross-validation, refit
included, which the scaffold does not do.

**The question to carry to your own data is what one row is.** If several rows
describe the same person, session, or device, that identifier is the group,
whether or not the file gives it to you as a column. If rows genuinely are
independent, set `group_col` to `None`. What the split should approximate is how
the model gets used ([Little et al., GigaScience 6(5):gix020,
2017](https://academic.oup.com/gigascience/article/6/5/gix020/3073663)), and here
that is a person the model has never heard.
