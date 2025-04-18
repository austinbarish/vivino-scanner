import pandas as pd
import streamlit as st
import altair as alt
import google.generativeai as genai
import PyPDF2
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Import functions.py
from functions import *


# Intro Page to upload the wine scan
def intro():
    st.write(
        "Welcome to the Wine Scanner! Please upload your wine list PDF file to get started."
    )

    # Check for temp folder
    if not os.path.exists("temp"):
        os.makedirs("temp")

    # Check for upload and outputs folder
    if not os.path.exists("./temp/uploads"):
        os.makedirs("./temp/uploads")
    if not os.path.exists("./temp/outputs"):
        os.makedirs("./temp/outputs")

    # File uploader
    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    if uploaded_file is not None:
        with open("./temp/uploads/uploaded_file.pdf", "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success("File uploaded successfully!")

    # If a file is uploaded, run the scan
    if uploaded_file is not None:
        # Run the scan
        if st.button("Scan"):
            with st.spinner("Scanning..."):
                # Call the function to scan the PDF and save the results
                df = create_csv_menu(
                    "./temp/uploads/uploaded_file.pdf",
                    "./temp/uploads/uploaded_file.csv",
                    editor=False,
                )
                st.success("Scan complete!")

            # Show the csv
            st.write("Here is the scanned data:")
            st.dataframe(df)

    # Offer to filter by wine type, size, or price
    if os.path.exists("./temp/uploads/uploaded_file.csv"):
        st.write(
            "Checking for ratings takes time. You can filter the data by wine type, size, or price now to save time. You will see the filters automatically update as you edit them (ex: you won't be able to select champagne if it is not in your price range) Note: Once you click the button below, you will not be able to change the filters for the ratings."
        )
        scanned_df = pd.read_csv("./temp/uploads/uploaded_file.csv")

        # Select Price
        scanned_df["price"] = scanned_df["price"].apply(
            lambda x: float(x) if x != "N/A" else 0
        )
        # Get the max price
        max_price = scanned_df["price"].max()
        # Get the min price
        min_price = scanned_df["price"].min()
        # Add a slider to filter by price
        price_slider = st.slider(
            "Select Price Range",
            min_value=min_price,
            max_value=max_price,
            value=(min_price, max_price),
            step=1.0,
            format="$%.0f",  # Formats values as $XX.XX
            key="price_slider",
        )
        # Filter scanned df by price
        scanned_df = scanned_df[
            (scanned_df["price"] >= price_slider[0])
            & (scanned_df["price"] <= price_slider[1])
        ]

        # Select Main Types
        main_types = scanned_df["main_type"].unique()
        main_types = [
            x for x in main_types if x != "N/A" and x != "" and x != " " and x != "nan"
        ]
        # Sort to have Red and White first always then other
        main_types = sorted(
            main_types,
            key=lambda x: (x not in ["RED", "WHITE"], x),
        )
        # Add a multiselect to filter by main type
        main_types_choice = st.pills(
            "Select Wine Types",
            main_types,
            selection_mode="multi",
            default=main_types,
            key="main_types",
        )

        # Filter scanned df by main types
        scanned_df = scanned_df[scanned_df["main_type"].isin(main_types_choice)]

        # Select Sizes
        sizes = scanned_df["size"].unique()
        sizes = [x for x in sizes if x != "N/A"]
        size_choice = st.pills(
            "Select Sizes", sizes, selection_mode="multi", default=sizes, key="sizes"
        )
        # Filter scanned df by sizes
        scanned_df = scanned_df[scanned_df["size"].isin(size_choice)]

        # Filter by grape
        grapes = scanned_df["type"].unique()
        grapes = [
            x for x in grapes if x != "N/A" and x != "" and x != " " and x != "nan"
        ]
        grape_choice = st.pills(
            "Select Grapes",
            grapes,
            selection_mode="multi",
            default=grapes,
            key="grapes",
        )
        # Filter scanned df by grapes
        scanned_df = scanned_df[scanned_df["type"].isin(grape_choice)]

    # Show a button to get ratings
    if st.button("Get Ratings"):
        df = pd.read_csv("./temp/uploads/uploaded_file.csv")

        # Filter the data
        df = df[
            (df["main_type"].isin(main_types_choice))
            & (df["size"].isin(size_choice))
            & (df["price"] >= price_slider[0])
            & (df["price"] <= price_slider[1])
        ]

        # Count entries and calculate estimated time
        entries = len(df)
        st.write(
            f"Given {entries} entries, this will take about {round(entries / 60, 1)} minutes."
        )
        st.write("Feel free to go grab a drink while you wait!")

        with st.spinner("Getting ratings..."):
            # Call the function to get the ratings
            viv_df = vivino_search_all(df)
            st.success("Ratings complete!")
            st.balloons()

        # Show the csv
        st.write("Here is the scanned data with ratings:")
        st.dataframe(df)

        # Save output
        df.to_csv("./temp/outputs/output.csv", index=False)

        # Save the data to a csv
        viv_df.to_csv("./temp/outputs/output.csv", index=False)

        # Give the option to download the csv to save time
        output_csv = viv_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Download CSV if you want to skip this step next time",
            data=output_csv,
            file_name="scanned_wines.csv",
            mime="text/csv",
            icon=":material/download:",
        )

        # Show a button to go to the post scan page
        st.write("To go to post scan page, change the button on the left")


# Page for after the wine scan is complete
# @st.cache_data
def post_scan():
    upload = False

    # Check for if output was already made
    if not os.path.exists("./temp/outputs/output.csv"):
        st.write(
            "Please upload a PDF file and run the scan before going to this page. Or, upload a previous csv below"
        )
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
        if uploaded_file is not None:
            with open("./temp/uploads/output.csv", "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success("File uploaded successfully!")
            st.write("Checking compatibility...")

            # Make sure the columns are correct
            df = pd.read_csv("./temp/uploads/output.csv")

            required_columns = {
                "producer",
                "name",
                "menu_price",
                "vivino_price",
                "rating",
            }
            if required_columns.issubset(df.columns):
                st.success("File is compatible!")
                upload = True
            else:
                st.error(
                    "File is not compatible! Please upload a file with the correct columns."
                )

    else:
        # Load the data
        df = pd.read_csv("./temp/outputs/output.csv")
        print(df.columns)
        upload = True

    # Don't start until the file is uploaded
    if upload:
        # Make sure menu_price, vivino_price, price_multiplier, and rating are floats, if not, set as 0
        df["menu_price"] = df["menu_price"].apply(
            lambda x: float(x) if x != "N/A" else 0
        )
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

        # Get columns
        columns = df.columns.tolist()

        # If there are no ids, remove the column
        if "id" in columns:
            if len(df["id"].unique()) <= 2:
                df = df.drop(columns=["id"])

        # Create a sidebar
        st.sidebar.title("Filters")

        # Let user pick x and y axis with default x is price and y is rating with another option of price multiplier or number of reviews
        x_axis = st.sidebar.selectbox(
            "X Axis",
            ["menu_price", "rating", "price_multiplier", "num_ratings"],
            key="x",
        )

        # Default y axis is rating
        y_axis = st.sidebar.selectbox(
            "Y Axis",
            ["rating", "menu_price", "price_multiplier", "num_ratings"],
            key="y",
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

        # Add pills to filter by size, default is all
        size = st.sidebar.pills(
            "Size",
            df["size"].unique(),
            selection_mode="multi",
            default=df["size"].unique(),
            key="size",
        )

        # Add pills to filter by main type, default is all
        wine_type = st.sidebar.pills(
            "Wine Type",
            df["main_type"].unique(),
            selection_mode="multi",
            default=df["main_type"].unique(),
            key="wine_type",
        )

        # Add pills to filter by grape, default is all
        grape = st.sidebar.pills(
            "Grape Varietal",
            df["type"].unique(),
            selection_mode="multi",
            default=df["type"].unique(),
            key="grape",
        )

        # Add pills to filter by country, default is all
        if "country" in df.columns:
            country = st.sidebar.pills(
                "Country",
                df["country"].unique(),
                selection_mode="multi",
                default=df["country"].unique(),
                key="country",
            )

        # Add pills to filter by region, default is all
        region = st.sidebar.pills(
            "Region",
            df["region"].unique(),
            selection_mode="multi",
            default=df["region"].unique(),
            key="region",
        )

        # Main page, should fill the page with the filtered data
        st.write(f"## {len(df)} wines found")

        # Filter the data
        filtered_df = df[
            (df["menu_price"] >= price_slider[0])
            & (df["menu_price"] <= price_slider[1])
            & (df["main_type"].isin(wine_type) if "main_type" in df.columns else True)
            & (df["type"].isin(grape) if "type" in df.columns else True)
            & (df["country"].isin(country) if "country" in df.columns else True)
            & (df["region"].isin(region) if "region" in df.columns else True)
            & (df["size"].isin(size) if "size" in df.columns else True)
            & (df["rating"] >= rating_slider[0] if "rating" in df.columns else True)
            & (df["rating"] <= rating_slider[1] if "rating" in df.columns else True)
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
                x=alt.X(
                    x_axis, title=x_axis.replace("_", " ").title()
                ),  # Need to make 0 to 5 for rating in the future
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
                    alt.Tooltip("vintage", title="Vintage"),
                    alt.Tooltip("rating", title="Rating"),
                    alt.Tooltip(
                        "menu_price", title="Price", format="$,.2f"
                    ),  # Format as currency
                ]
                + (
                    [alt.Tooltip("country", title="Country")]
                    if "country" in filtered_df.columns
                    else []
                ),
            )
            .interactive()
        )

        st.altair_chart(chart, use_container_width=True)

        # Make Food Pairings Prettier and last column
        filtered_df["food_pairings"] = filtered_df["food_pairings"].apply(
            lambda x: " ".join(
                (
                    word.capitalize()
                    if word.lower() not in ["and", "or", "etc"]
                    else word.lower()
                )
                for word in x.replace("[", "").replace("]", "").replace("'", "").split()
            )
        )

        # Move food pairings to the last column
        food_pairings = filtered_df.pop("food_pairings")
        filtered_df["food_pairings"] = food_pairings

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
