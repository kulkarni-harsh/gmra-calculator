import os

import matplotlib
import pandas as pd
import seaborn as sns

from app.core.types import SexAgeCounts

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def create_population_df(data):
    """Converts the nested dictionary into a long-format DataFrame."""
    # Extract age categories excluding the 'Total' key
    age_categories = [k for k in data["M"].keys() if k != "Total"]

    rows = []
    for age in age_categories:
        rows.append({"Age Group": age, "Gender": "Male", "Population": data["M"][age]})
        rows.append({"Age Group": age, "Gender": "Female", "Population": data["F"][age]})

    pop_df = pd.DataFrame(rows)
    pop_df["Age Group"] = pop_df["Age Group"].replace(
        "85-1000",
        "85+",
    )
    return pop_df


def plot_population_distribution(combined_demographics_dict: SexAgeCounts, png_path: str) -> str:
    """Plot the population distribution by age and gender and save it as a PNG file."""
    demographic_population_df = create_population_df(combined_demographics_dict)

    sns.set_theme(style="whitegrid")
    fig = plt.figure(figsize=(14, 7))

    # Create grouped bar chart
    plot = sns.barplot(
        data=demographic_population_df,
        x="Age Group",
        y="Population",
        hue="Gender",
        palette=["#3498db", "#e74c3c"],  # Professional Blue and Red/Coral
    )

    # Customization for PPT
    plt.title(
        "Population Distribution by Age and Gender",
        fontsize=18,
        fontweight="bold",
        pad=20,
    )
    plt.xlabel("Age Group", fontsize=14, fontweight="bold")
    plt.ylabel("Population Count", fontsize=14, fontweight="bold")
    plt.xticks(rotation=45)
    plt.legend(title="Gender", title_fontsize="13", fontsize="11")

    # Add value labels on top of each bar, offsetting to avoid overlap
    patches = plot.patches
    for i, p in enumerate(patches):
        height = p.get_height()
        if height > 0:
            # Alternate offset for each gender in the group
            offset = 6 if i % 2 == 0 else 12
            plot.annotate(
                format(int(height), ","),
                (p.get_x() + p.get_width() / 2.0, height),
                ha="center",
                va="center",
                xytext=(0, offset),
                textcoords="offset points",
                fontsize=8,
                rotation=0,
            )

    plt.tight_layout()
    plt.savefig(png_path, dpi=300)
    plt.close(fig)
    return os.path.abspath(png_path)
