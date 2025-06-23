import matplotlib.pyplot as plt
import numpy as np

# Данные
years = [2021, 2022, 2023, 2024]
total_teachers = [1311282, 1304835, 1301172, 1304835]

# График 1: Гистограмма общей численности педагогических работников
plt.figure(figsize=(8, 5))
plt.bar(years, total_teachers, color='skyblue')
plt.title('Общая численность педагогических работников по годам')
plt.xlabel('Год')
plt.ylabel('Численность')
plt.xticks(years)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.show()

# График 2: Расчет и построение графика ежегодного изменения в процентах
total_teachers = np.array(total_teachers)
annual_change_percent = (total_teachers[1:] - total_teachers[:-1]) / total_teachers[:-1] * 100

plt.figure(figsize=(8, 5))
plt.plot(years[1:], annual_change_percent, marker='o', linestyle='-', color='green')
plt.title('Ежегодное изменение численности педагогических работников (%)')
plt.xlabel('Год')
plt.ylabel('Изменение (%)')
plt.grid(True, linestyle='--', alpha=0.7)
plt.xticks(years[1:])
plt.show()

# График 3: Сравнительный график распределения по стажу (stacked bar chart)
experience_categories = ["до 3 лет", "от 3 до 5 лет", "от 5 до 10 лет", 
                         "от 10 до 15 лет", "от 15 до 20 лет", "20 и более лет"]
experience_data = {
    2021: [130963, 83900, 155631, 135692, 127202, 677894],
    2022: [135957, 84449, 154904, 140292, 123341, 665892],
    2023: [140565, 84029, 152914, 142543, 123262, 657859],
    2024: [135957, 84449, 154904, 140292, 123341, 665892]
}

plt.figure(figsize=(10, 6))
bottom = np.zeros(len(years))

for category in experience_categories:
    values = [experience_data[year][experience_categories.index(category)] for year in years]
    plt.bar(years, values, bottom=bottom, label=category)
    bottom += np.array(values)

plt.title('Распределение педагогов по стажу работы по годам')
plt.xlabel('Год')
plt.ylabel('Численность')
plt.legend(title='Стаж работы')
plt.xticks(years)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.show()
