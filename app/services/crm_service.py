"""
CRM Service

This service acts as a high-level wrapper over the Excel file using the 'pandas' library.
It is responsible for modifying and querying the CRM lead spreadsheet in a robust tabular format.

Key Features & Operations:
--------------------------
1. Load DataFrame (load): Reads the Excel file into a Pandas DataFrame and forces string columns 
   (like Status, Call Status, Last Call SID, Objections, etc.) to behave as generic objects. This prevents 
   Pandas from misinterpreting missing fields as floats (e.g. NaN) and crashing during updates.
2. Save DataFrame (save): Writes the Pandas DataFrame back to the Leads.xlsx file, preserving sheet index alignment.
3. Update Lead (update_lead): Finds the row matching a specific Lead ID and conditionally updates columns 
   (Status, Qualification, Summary, Objections, Requirements, etc.) ONLY if they are present in the update payload.
4. Upsert Lead (upsert_lead): If the Lead ID is found, it updates the row; otherwise, it appends a brand new row to the sheet.
"""

from datetime import datetime, timezone, timedelta

import pandas as pd

from app.core.config import settings


class CRMService:
    """
    Excel CRM Service.
    """

    def __init__(self):

        self.file = settings.excel_file

    # -------------------------------------------------

    def load(self):
        df = pd.read_excel(self.file)
        # Prevent dtype conversion errors for string fields
        string_cols = [
            "Last Call SID", "Call Status", "Status", "Lead Qualification", 
            "Conversation Summary", "Customer Requirements", "Objections Raised",
            "Email", "City", "Name", "Last Contacted Timestamp", "Meeting Date & Time",
            "Follow-up Date", "Company"
        ]
        for col in string_cols:
            if col in df.columns:
                df[col] = df[col].astype(object)
        return df

    # -------------------------------------------------

    def save(
        self,
        df,
    ):

        df.to_excel(
            self.file,
            index=False,
        )

    # -------------------------------------------------

    def update_lead(
        self,
        lead_id: int,
        crm_update: dict,
    ):

        df = self.load()

        idx = df.index[
            df["Lead ID"] == lead_id
        ]

        if len(idx) == 0:

            raise ValueError(
                f"Lead {lead_id} not found."
            )

        row = idx[0]

        # ------------------------
        # Status
        # ------------------------

        if "status" in crm_update:

            df.loc[
                row,
                "Status",
            ] = crm_update["status"]

        # ------------------------
        # Qualification
        # ------------------------

        if "qualification" in crm_update:

            df.loc[
                row,
                "Lead Qualification",
            ] = crm_update[
                "qualification"
            ]

        # ------------------------
        # Summary
        # ------------------------

        if "summary" in crm_update:

            df.loc[
                row,
                "Conversation Summary",
            ] = crm_update[
                "summary"
            ]

        # ------------------------
        # Objection
        # ------------------------

        if "objection" in crm_update:

            df.loc[
                row,
                "Objections Raised",
            ] = crm_update[
                "objection"
            ]

        # ------------------------
        # Requirement
        # ------------------------

        if "requirement" in crm_update:

            df.loc[
                row,
                "Customer Requirements",
            ] = crm_update[
                "requirement"
            ]

        # ------------------------
        # Meeting
        # ------------------------

        if "meeting" in crm_update:

            df.loc[
                row,
                "Meeting Date & Time",
            ] = crm_update[
                "meeting"
            ]

        # ------------------------
        # Follow Up
        # ------------------------

        if "follow_up" in crm_update:

            df.loc[
                row,
                "Follow-up Date",
            ] = crm_update[
                "follow_up"
            ]

        # ------------------------
        # Call status/retries
        # ------------------------

        if "call_status" in crm_update:
            df.loc[row, "Call Status"] = crm_update["call_status"]

        if "retry_count" in crm_update:
            df.loc[row, "Retry Count"] = crm_update["retry_count"]

        if "last_call_sid" in crm_update:
            df.loc[row, "Last Call SID"] = crm_update["last_call_sid"]

        # ------------------------
        # Last Contact
        # ------------------------

        ist = timezone(timedelta(hours=5, minutes=30))
        df.loc[
            row,
            "Last Contacted Timestamp",
        ] = datetime.now(ist).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        self.save(df)

        return True

    # -------------------------------------------------

    def upsert_lead(
        self,
        lead_id,
        crm_update,
    ):

        df = self.load()

        idx = df.index[
            df["Lead ID"].astype(str) == str(lead_id)
        ]

        if len(idx) == 0:

            new_row = {

                "Lead ID": lead_id,

                "Status": crm_update.get("status", "Pending"),

                "Lead Qualification": crm_update.get("qualification", "Warm"),

                "Conversation Summary": crm_update.get("summary", ""),

                "Customer Requirements": crm_update.get("requirement", ""),

                "Objections Raised": crm_update.get("objection", ""),

                "Meeting Date & Time": crm_update.get("meeting", ""),

                "Follow-up Date": crm_update.get("follow_up", ""),

                "Call Status": crm_update.get("call_status", ""),

                "Retry Count": crm_update.get("retry_count", 0),

                "Last Call SID": crm_update.get("last_call_sid", ""),

                "Last Contacted Timestamp": datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%Y-%m-%d %H:%M:%S"),

            }

            df = pd.concat(

                [df, pd.DataFrame([new_row])],

                ignore_index=True,

            )

        else:

            row = idx[0]

            if "status" in crm_update:
                df.loc[row, "Status"] = crm_update["status"]

            if "qualification" in crm_update:
                df.loc[row, "Lead Qualification"] = crm_update["qualification"]

            if "summary" in crm_update:
                df.loc[row, "Conversation Summary"] = crm_update["summary"]

            if "requirement" in crm_update:
                df.loc[row, "Customer Requirements"] = crm_update["requirement"]

            if "objection" in crm_update:
                df.loc[row, "Objections Raised"] = crm_update["objection"]

            if "meeting" in crm_update:
                df.loc[row, "Meeting Date & Time"] = crm_update["meeting"]

            if "follow_up" in crm_update:
                df.loc[row, "Follow-up Date"] = crm_update["follow_up"]

            if "call_status" in crm_update:
                df.loc[row, "Call Status"] = crm_update["call_status"]

            if "retry_count" in crm_update:
                df.loc[row, "Retry Count"] = crm_update["retry_count"]

            if "last_call_sid" in crm_update:
                df.loc[row, "Last Call SID"] = crm_update["last_call_sid"]

            ist = timezone(timedelta(hours=5, minutes=30))
            df.loc[row, "Last Contacted Timestamp"] = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")

        self.save(df)

    # -------------------------------------------------

    def get_lead(
        self,
        lead_id: int,
    ):

        df = self.load()

        row = df[
            df["Lead ID"] == lead_id
        ]

        if row.empty:

            return None

        return row.iloc[0].to_dict()