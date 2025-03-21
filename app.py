import pandas as pd
import streamlit as st
import altair as alt
import google.generativeai as genai
import PyPDF2
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import seaborn as sns

# Import functions.py
from functions import *


# Intro Page to upload the wine scan
def intro():
    st.title("Wine Scanner")
    st.write(
        "Welcome to the Wine Scanner! Please upload your wine list PDF file to get started."
    )

    # File uploader
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    # Save the uploaded file
    if uploaded_file is not None:
        with open("uploaded_file.pdf", "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success("File uploaded successfully!")

    # If a file is uploaded, run the scan
    if uploaded_file is not None:
        # Run the scan
        if st.button("Scan"):
            with st.spinner("Scanning..."):
                # Call the function to scan the PDF and save the results
                df = create_csv_menu("uploaded_file.pdf", editor=False)
                st.success("Scan complete!")
                st.balloons()

            # Show the csv
            st.write("Here is the scanned data:")
            st.dataframe(df)

            # Show a button to go to the post scan page
            if st.button("Go to Post Scan"):
                post_scan()


# Page for after the wine scan is complete
@st.cache_data
def post_scan():
    st.title("Wine Scanner")

    # Load the data
    df = pd.read_csv("uploaded_file.csv")

    # Make sure menu_price, vivino_price, price_multiplier, and rating are floats, if not, set as 0
    df["menu_price"] = df["menu_price"].apply(lambda x: float(x) if x != "N/A" else 0)
    df["vivino_price"] = df["vivino_price"].apply(
        lambda x: float(x) if x != "N/A" else 0
    )
    df["price_multiplier"] = df["price_multiplier"].apply(
        lambda x: float(x) if x != "N/A" else 0
    )

    # Make sure rating is a float, if not, set as 0
    ratings = []
    for rating in df["rating"]:
        if rating != "-" and rating != "N/A":
            try:
                ratings.append(float(rating))
            except:
                ratings.append(0)
        else:
            ratings.append(0)
    df["rating"] = ratings

    # If there are no ids, remove the column
    if len(df["id"].unique()) <= 2:
        df = df.drop(columns=["id"])
    # df["num_ratings"] = df["num_ratings"].apply(lambda x: float(x) if x != "N/A" else 0)

    # Create a sidebar
    st.sidebar.title("Filters")

    # Let user pick x and y axis with default x is price and y is rating with another option of price multiplier or number of reviews
    x_axis = st.sidebar.selectbox(
        "X Axis", ["menu_price", "rating", "price_multiplier", "num_ratings"]
    )

    # Default y axis is rating
    y_axis = st.sidebar.selectbox(
        "Y Axis", ["rating", "menu_price", "price_multiplier", "num_ratings"]
    )

    # Add a slider to filter by price
    price_slider = st.sidebar.slider(
        "Price",
        min_value=0.0,
        max_value=max(df["menu_price"]),
        value=(0.0, max(df["menu_price"])),
        format="$%.0f",  # Formats values as $XX.XX
    )

    # Add a range slider to filter by rating, default is 0 to 5
    rating_slider = st.sidebar.slider(
        "Rating", min_value=0.0, max_value=5.0, value=(0.0, 5.0), format="%.1f"
    )

    # Add multi-select to filter by size, default is all
    size = st.sidebar.multiselect(
        "Size", df["size"].unique(), default=df["size"].unique()
    )

    # Add a multi-select to filter by main type, default is all
    wine_type = st.sidebar.multiselect(
        "Wine Type", df["main_type"].unique(), default=df["main_type"].unique()
    )

    # Add a multi-select to filter by country, default is all
    country = st.sidebar.multiselect(
        "Country", df["country"].unique(), default=df["country"].unique()
    )

    # Add a multi-select to filter by region, default is all
    region = st.sidebar.multiselect(
        "Region", df["region"].unique(), default=df["region"].unique()
    )

    # Main page, should fill the page with the filtered data
    st.write(f"## {len(df)} wines found")

    # Filter the data
    filtered_df = df[
        (df["menu_price"] >= price_slider[0])
        & (df["menu_price"] <= price_slider[1])
        & (df["main_type"].isin(wine_type))
        & (df["country"].isin(country))
        & (df["region"].isin(region))
        & (df["rating"] >= rating_slider[0])
        & (df["rating"] <= rating_slider[1])
    ]

    # Add color column to the filtered data by main_type (red, white, rose, sparkling, orange, or other)
    color_map = {
        "red": "#7B1E26",
        "white": "#F4E19C",
        "sparkling": "#F7D07D",
        "rose": "#E88E9B",
        "orange": "#E07E39",
        "other": "#808080",  # Default gray for unspecified types
    }

    filtered_df["color"] = (
        filtered_df["main_type"]
        .str.lower()
        .map(lambda x: color_map.get(x, color_map["other"]))
    )

    # Add a scatter plot with tooltips showing wine details

    chart = (
        alt.Chart(filtered_df)
        .mark_circle()
        .encode(
            x=alt.X(x_axis, title=x_axis.replace("_", " ").title()),
            y=alt.Y(y_axis, title=y_axis.replace("_", " ").title()),
            color=alt.Color("color", scale=None),
            size=alt.Size(
                "menu_price", scale=alt.Scale(range=[10, 300])
            ),  # Adjust size dynamically
            tooltip=[
                alt.Tooltip("producer", title="Producer"),
                alt.Tooltip("name", title="Name"),
                alt.Tooltip("type", title="Type"),
                alt.Tooltip("region", title="Region"),
                alt.Tooltip("country", title="Country"),
                alt.Tooltip("vintage", title="Vintage"),
                alt.Tooltip(
                    "menu_price", title="Price", format="$,.2f"
                ),  # Format as currency
            ],
        )
        .interactive()
    )

    st.altair_chart(chart, use_container_width=True)

    # Remove _ from the column names
    filtered_df.columns = filtered_df.columns.str.replace("_", " ")

    # Title each column
    filtered_df.columns = filtered_df.columns.str.title()

    # Display the filtered data
    st.dataframe(filtered_df.drop(columns=["Color"]), use_container_width=True)


# Main function to run the app
def main():
    st.set_page_config(page_title="Wine Scanner", layout="wide")
    st.title("Wine Scanner")

    # Create a menu
    menu = ["Intro", "Post Scan"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Intro":
        intro()
    elif choice == "Post Scan":
        post_scan()


if __name__ == "__main__":
    main()
