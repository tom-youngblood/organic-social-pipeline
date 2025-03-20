import requests
import pandas as pd
from google.cloud import bigquery
import funcs

def main():
    # Query BigQuery for contact information and Post Names to send to Hubspot
    query = """
            SELECT
                c.*,
                p.postName
            FROM
                `skilled-tangent-448417-n8.pb_dataset.contacts` AS c
            LEFT JOIN
                `skilled-tangent-448417-n8.pb_dataset.posts` AS p
            ON
                c.postId = p.postId;
            """

    # Save BigQuery Leads, dropping duplicates if exist
    bq_leads = funcs.BQ.bq_query_table("../config/skilled-tangent-448417-n8-35dde3932757.json", query).drop_duplicates(subset="profileLink")

    # HubSpot API URL for fetching all contacts in a list
    list_id = 246
    url = f"https://api.hubapi.com/contacts/v1/lists/{list_id}/contacts/all?property=hs_linkedin_url"
    api_key, headers, url = funcs.HS.hs_prepare_request(url, "../config/hs_key.txt")

    # Fetch all contacts from the HubSpot list
    all_contacts = funcs.HS.hs_fetch_list_contacts(api_key, headers, url, list_id)
    print(f"Total Contacts Retrieved: {len(all_contacts)}")

    # Subset of contacts that are in BQ and not HS (new leads)
    hs_li_links = [contact.get("properties", {}).get("hs_linkedin_url", {}).get("value", "").strip() for contact in all_contacts]
    new_leads = bq_leads.loc[(~bq_leads["profileLink"].isin(hs_li_links))]
    print(f"Number of leads to push: {len(new_leads)}")

    # Push new leads to hubspot
    funcs.HS.hs_push_contacts_to_list(api_key, new_leads)

if __name__ == "__main__":
    main()
