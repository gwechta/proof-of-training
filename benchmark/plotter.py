import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

if __name__ == "__main__":
    data = pd.read_csv("data.csv")

    # Create a seaborn plot
    sns.set(font_scale=1.4, style="whitegrid")  # Set the style of the plot
    data["n"] = data["n"].astype(int)

    # Plot
    plt.figure(figsize=(10, 6))  # Adjust the figure size if needed
    sns.lineplot(data=data, x="n", y="td", marker="o", label="training declarations")
    sns.lineplot(data=data, x="n", y="bh", marker="o", label="block headers")
    sns.lineplot(data=data, x="n", y="forks", marker="o", label="forks")

    # Add labels and title
    plt.xlabel("Nodes Number")
    plt.ylabel("Protocol Messages")
    plt.title("Plot of Nodes Number vs. Protocol Messages")

    # Add legend
    plt.legend()
    plt.gca().xaxis.set_major_locator(MaxNLocator(integer=True, nbins=20))

    plt.savefig("plot.svg", format="svg")
    # Show plot
    plt.show()
