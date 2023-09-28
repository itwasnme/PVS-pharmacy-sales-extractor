'''
What general info are we looking for?
1) Percentage of controlled vs non-controlled
   - Percentage of cash payments for controlled substances
2) Top 5 prescribers for controlled substances
   - Monotonous Prescribing. When over 30% of a doctor's prescriptions are exactly the same.
3) Spatial concerns (Greater than 100 miles)
4) # of Scripts per days
5) Oxy units per month  (flag = max 5800 DU Oxys per month (30 days of open pharmacy))
6) Hydro units per month (flag = max 7200 DU Hydros per month (30 days of open pharmacy))


What combos we looking for?

1) Combination of 2 or more short acting pain medication
2) Trinity Combo: Combination of Muscle Relaxer, Pain Medication, and Sleeping Medication. (usually the muscle relaxer would be Carisoprodol)
3) Patient's receiving CS RX from different prescribers.
4) Phentermine. Red flag if it's more than 1 pill/day
5) High dosages of oxy and hydro. (Prescriptions over 180 DU and above 6 pills/day)


What are the exemptions?

1) Oral Solution, liquid, and Patches are not major concerns.
2) Methadone is always Long Acting (extended release).
3) Prescriptions that are not major concerns in up to 6 pills/day:
  - PREGABALIN
  - AMPHETAMINE 
  - LISDEXAMFETAMINE 
  - BENZODIAZEPINES
  - TESTOSTERONE 
  - ZOLPIDEM
  - TRAMADOL
  - PROMETHAZINE
  - ACETAMINOPHEN
'''

import pandas as pd
import numpy as np
file = open('output.txt', 'w')

file_name = input("Enter file name: ")
df = pd.read_csv (file_name)
columnds_to_drop = ['NDC', 'DEA#', 'Family Old', 'Family 6', 'Family 8', 'Family 10']
df = df.drop(columns=columnds_to_drop)

#Scripts per day
df['Fill Date'] = pd.to_datetime(df['Fill Date'])
unique_dates_count = df['Fill Date'].nunique()
num_rows = df.shape[0] 
scripts_per_day = int(num_rows / unique_dates_count)
file.write("(1) NUMBER OF SCRIPTS PER DAY: " + str(scripts_per_day) + "\n")

file.write("\n\n")

# Controlled percentage
total_rows = len(df)
filtered_df = df.dropna(subset=['Family'])
controlled_rows = len(filtered_df)
percentage = (controlled_rows / total_rows) * 100
file.write(f"(2) PERCENTAGE OF CONTROLLED SUBSTANCES SOLD: {percentage:.2f}% \n")

file.write("\n\n")

# Cash percentage
filtered_df = df.dropna(subset=['Family'])
total_rows = len(filtered_df)
cash_rows = len(filtered_df[filtered_df['Pay Type'] == 'CASH'])
percentage = (cash_rows / total_rows) * 100
file.write(f"(3) PERCENTAGE OF CONTROLLED SUBSTANCES PAID IN CASH: {percentage:.2f}% \n")

file.write("\n\n")

# Top five doctors for CS
file.write("(4) TOP FIVE DOCTORS FOR CONTROLLED SUBTANCES (DOSAGE UNITS): \n\n")
filtered_df = df.dropna(subset=['Family'])
top_prescribers = filtered_df.groupby('Physician Name')['Qty'].sum().nlargest(5)
top_prescribers_str = top_prescribers.to_string()
file.write(top_prescribers_str + "\n")

file.write("\n\n")

# Monotonous precribing (Only consider prescribers with 15 or more prescriptions)
filtered_df = df.dropna(subset=['Family'])
prescriber_counts = filtered_df['Physician Name'].value_counts()
prescribers_over_14_prescriptions = prescriber_counts[prescriber_counts > 14].index
filtered_df = filtered_df[filtered_df['Physician Name'].isin(prescribers_over_14_prescriptions)]
grouped = filtered_df.groupby(['Physician Name', 'Drug Name', 'Days Supply', 'Qty']).size() / filtered_df.groupby('Physician Name').size() * 100
result = grouped[grouped > 30]
if not result.empty:
    file.write("(5) PRESCRIBERS AND CORRESPONDING CS WITH OVER 30% OF PRESCRIPTIONS: \n\n")
    for index, row in result.reset_index().iterrows():
        prescriber = row['Physician Name']
        drug = row['Drug Name']
        percentage = row[0]
        file.write(f"Prescriber: {prescriber}, Drug: {drug}, Percentage: {percentage:.4f}% \n")
else:
    file.write("(5) NO PRESCRIBER HAS PRESCRIBED ANY CONTROLLED SUBSTANCE OVER 30% OF THE TIME. \n")

    
file.write("\n\n")

# Spatial concerns (Greater than 100 miles)
file.write("(6) SPATIAL CONCERNS: \n\n")
filtered_df = df.dropna(subset=['Family'])
filtered_df = filtered_df.replace({'': np.nan, '-': np.nan})
filtered_df[filtered_df.columns[-3:]] = filtered_df[filtered_df.columns[-3:]].apply(pd.to_numeric, errors='coerce')
filtered_df = filtered_df[filtered_df.iloc[:, -3:].apply(lambda row: any(row > 100), axis=1)]
filtered_df = filtered_df.sort_values(by='Patient ID')
for index, row in filtered_df.iterrows():
    patient_id = row['Patient ID']
    over_100_columns = []
    for col in filtered_df.columns[-3:]:
        if not pd.isna(row[col]) and row[col] > 100:
            over_100_columns.append(col)
    if over_100_columns:
        file.write(f"Patient ID: {patient_id}, received a prescription where the distance was over 100 miles between: {', '.join(over_100_columns)} \n")

file.write("\n\n")

#Oxy units per month
months = unique_dates_count/30
sum_qty_oxycodone = df[(df['Family'] == 'OXYCODONE') & (df['Drug Name'].str.contains('Tablet'))]['Qty'].sum()
oxy_per_month = int(sum_qty_oxycodone/months)
file.write(f"(7) AVERAGE DOSAGE UNITS FOR OXYCODONE FAMILY PER MONTH: {oxy_per_month} \n")

file.write("\n\n")

#Hydro units per month
months = unique_dates_count/30
sum_qty_hydrocodone = df[(df['Family'] == 'HYDROCODONE') & (df['Drug Name'].str.contains('Tablet'))]['Qty'].sum()
hydro_per_month = int(sum_qty_hydrocodone/months)
file.write(f"(8) AVERAGE DOSAGE UNITS FOR HYDROCODONE FAMILY PER MONTH: {hydro_per_month} \n")

file.write("\n\n")

#2 or more short acting pain medication
file.write("(9) PATIENTS RECEIVING A COMBINATION OF TWO OR MORE SHORT-ACTING PAIN MEDICATION: \n\n")
filtered_df = df.dropna(subset=['Family'])
filtered_df = filtered_df[(~filtered_df['Drug Name'].str.contains('Solution')) & (~filtered_df['Drug Name'].str.contains('Liquid')) & (~filtered_df['Drug Name'].str.contains('Patch')) 
                          & (~filtered_df['Drug Name'].str.contains('ER')) & (~filtered_df['Family'].str.contains('PREGABALIN')) & (~filtered_df['Family'].str.contains('TESTOSTERONE'))
                          & (~filtered_df['Family'].str.contains('BENZODIAZEPINES')) & (~filtered_df['Family'].str.contains('PROMETHAZINE')) 
                          & (~filtered_df['Family'].str.contains('ZOLPIDEM')) & (~filtered_df['Family'].str.contains('AMPHETAMINE')) & (~filtered_df['Family'].str.contains('LISDEXAMFETAMINE'))
                          & (~filtered_df['Family'].str.contains('TRAMADOL')) & (~filtered_df['Family'].str.contains('ACETAMINOPHEN')) & (~filtered_df['Family'].str.contains('CARISOPRODOL'))
                          & (~filtered_df['Family'].str.contains('CLONAZEPAM')) & (~filtered_df['Family'].str.contains('METHADONE')) & (~filtered_df['Family'].str.contains('DIPHENOXYLATE'))
                          & (~filtered_df['Family'].str.contains('ISOMETHEPTENE')) & (~filtered_df['Family'].str.contains('ESZOPICLONE')) & (~filtered_df['Family'].str.contains('ZALEPLON'))
                          & (~filtered_df['Family'].str.contains('BUTALBITAL'))]
# Group the DataFrame by "Patient ID" and collect unique medications
patient_medication_groups = filtered_df.groupby('Patient ID')['Family'].unique()
# Iterate through the groups and print for patients with at least 2 unique medications
for patient_id, unique_medications in patient_medication_groups.items():
    if len(unique_medications) >= 2:
        file.write(f"Patient ID: {patient_id}, Medications: {', '.join(unique_medications)} \n")

file.write("\n\n")

#Trinity combinations
file.write("(10) 'HOLY TRINITY' COMBINATIONS: \n\n")
filtered_df = df.dropna(subset=['Family'])
filtered_df = filtered_df[(~filtered_df['Family'].str.contains('PREGABALIN')) & (~filtered_df['Family'].str.contains('TESTOSTERONE'))
                          & (~filtered_df['Family'].str.contains('PROMETHAZINE')) 
                          & (~filtered_df['Family'].str.contains('AMPHETAMINE')) & (~filtered_df['Family'].str.contains('LISDEXAMFETAMINE'))
                          & (~filtered_df['Family'].str.contains('ACETAMINOPHEN'))
                          & (~filtered_df['Family'].str.contains('CLONAZEPAM')) & (~filtered_df['Family'].str.contains('DIPHENOXYLATE'))
                          & (~filtered_df['Family'].str.contains('ISOMETHEPTENE')) & (~filtered_df['Family'].str.contains('BUTALBITAL'))]
# Group the DataFrame by "Patient ID" and collect unique medications
patient_medication_groups = filtered_df.groupby('Patient ID')['Family'].unique()
# Iterate through the groups and print for patients with at least 3 unique medications, including CARISOPRODOL
for patient_id, unique_medications in patient_medication_groups.items():
    if 'CARISOPRODOL' in unique_medications and ('BENZODIAZEPINES' in unique_medications or 'ESZOPICLONE' in unique_medications or 'ZALEPLON' in unique_medications or 'ZOLPIDEM' in unique_medications) and len(unique_medications) >= 3:
        file.write(f"Patient ID: {patient_id}, Medications: {', '.join(unique_medications)} \n")

file.write("\n\n")

# Number of patient's receiving CS RX from different prescribers.
filtered_df = df.dropna(subset=['Family'])
prescriber_counts = filtered_df.groupby(['Patient ID'])['Physician Name'].nunique()
patients_with_multiple_prescribers = prescriber_counts[prescriber_counts > 1]
total_patients_with_multiple_prescribers = len(patients_with_multiple_prescribers)
file.write("(11) TOTAL NUMBER OF PATIENTS WITH MULTIPLE PRESCRIBERS FOR CONTROLLED SUBSTANCES: " + str(total_patients_with_multiple_prescribers) + "\n")

file.write("\n\n")

# Phentermine. Red flag if it's more than 1 pill/day
phentermine_patients = df[(df['Drug Name'].str.contains('Phentermine', case=False)) & (df['Qty'] > df['Days Supply'])]
unique_phentermine_patients = phentermine_patients['Patient ID'].unique()
file.write("(12) PATIENT ID's WITH PHENTERMINE PRESCRIPTIONS FOR MORE THAN 1 PILL/DAY: ")
if(unique_phentermine_patients.size == 0):
    file.write("none \n")
else:
    file.write(str(unique_phentermine_patients) + "\n")

file.write("\n\n")

# Filter rows where Qty >= 180 and Family is 'OXYCODONE'
file.write("(13) PATIENTS RECEIVING A HIGH DOSAGE OF OXYCODONE: \n\n")
filtered_df = df[(df['Qty'] >= 180) & (df['Days Supply'] <= 90) & (df['Family'] == 'OXYCODONE') & (~df['Drug Name'].str.contains('Solution')) & (~df['Drug Name'].str.contains('Liquid'))]
result_df = filtered_df.groupby(['Patient ID', 'Drug Name', 'Qty', 'Days Supply']).size().reset_index(name='Number of Prescriptions')
result_df.sort_values(by='Patient ID', inplace=True)
result_df_str = result_df.to_string()
file.write(result_df_str + "\n")

file.write("\n\n")

# Filter rows where Qty >= 180 and Family is 'HYDROCODONE'
file.write("(14) PATIENTS RECEIVING A HIGH DOSAGE OF HYDROCODONE: \n\n")
filtered_df = df[(df['Qty'] >= 180) & (df['Days Supply'] <= 90) & (df['Family'] == 'HYDROCODONE') & (~df['Drug Name'].str.contains('Solution')) & (~df['Drug Name'].str.contains('Liquid'))]
result_df = filtered_df.groupby(['Patient ID', 'Drug Name', 'Qty', 'Days Supply']).size().reset_index(name='Number of Prescriptions')
result_df.sort_values(by='Patient ID', inplace=True)
result_df_str = result_df.to_string()
file.write(result_df_str)

file.close()