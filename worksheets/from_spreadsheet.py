import datetime
from enum import Enum
from typing import List

from worksheets.environment import (
    Action,
    GenieDB,
    GenieField,
    GenieRuntime,
    GenieType,
    GenieWorksheet,
    get_genie_fields_from_ws,
)
from worksheets.gsheet_utils import fill_all_empty, retrieve_gsheet

# Range of the gsheet
gsheet_range_default = "A1:AD1007"

# mapping of the columns
FORM_PREDICATE = 0
FORM_NAME = 1
FIELD_PREDICATE = 2
KIND = 3
FIELD_TYPE = 4
FIELD_NAME = 5
VARIABLE_ENUMS = 6
FIELD_DESCRIPTION = 7
DONT_ASK = 8
REQUIRED = 9
FIELD_CONFIRMATION = 10
FIELD_ACTION = 11
FORM_ACTION = 12
FIELD_VALIDATION = 13
EMPTY_COL = 14


def gsheet_to_classes(gsheet_id, gsheet_range=gsheet_range_default):
    """Convert Google Sheets data to Genie classes.

    Args:
        gsheet_id (str): The ID of the Google Sheet.
        gsheet_range (str): The range of cells to retrieve.

    Yields:
        Tuple[str, type]: The type of the class and the class itself."""
    rows = retrieve_gsheet(gsheet_id, gsheet_range)
    if not rows:
        raise ValueError("No data found.")

    rows = fill_all_empty(rows, EMPTY_COL + 1)

    # removing headers from the CSV
    rows = rows[1:]

    # collecting all the rows
    forms = []
    i = 0
    while i < len(rows):
        enums = []
        if len(rows[i][FORM_NAME]):
            forms.append(
                {
                    "form": rows[i],
                    "fields": [],
                    "outputs": [],
                }
            )
        else:
            if rows[i][FIELD_TYPE] == "Enum":
                enum_idx = i + 1
                while (
                    enum_idx < len(rows)
                    and not len(rows[enum_idx][FIELD_TYPE].strip())
                    and not len(rows[enum_idx][FIELD_NAME].strip())
                ):
                    enums.append(rows[enum_idx][VARIABLE_ENUMS])
                    enum_idx += 1

            if rows[i][KIND] == "output":
                forms[-1]["outputs"].append({"slottype": rows[i][FIELD_TYPE]})
            else:
                forms[-1]["fields"].append(
                    {
                        "slottype": (
                            rows[i][FIELD_TYPE]
                            if rows[i][FIELD_TYPE] != "Enum"
                            else create_enum_class(rows[i][FIELD_NAME], enums)
                        ),
                        "name": rows[i][FIELD_NAME],
                        "description": rows[i][FIELD_DESCRIPTION],
                        "predicate": rows[i][FIELD_PREDICATE],
                        "ask": not rows[i][DONT_ASK] == "TRUE",
                        "optional": not rows[i][REQUIRED] == "TRUE",
                        "actions": Action(rows[i][FIELD_ACTION]),
                        "value": None,
                        "requires_confirmation": rows[i][FIELD_CONFIRMATION] == "TRUE",
                        "internal": False if rows[i][KIND].lower() == "input" else True,
                        "primary_key": (
                            True if "primary" in rows[i][KIND].lower() else False
                        ),
                        "validation": (
                            None
                            if len(rows[i][FIELD_VALIDATION].strip()) == 0
                            else rows[i][FIELD_VALIDATION]
                        ),
                    }
                )
        if len(enums):
            i = enum_idx
        else:
            i += 1

    # creating the genie worksheet
    for form in forms:
        class_name = form["form"][FORM_NAME].replace(" ", "")
        form_predicate = form["form"][FORM_PREDICATE]
        form_action = Action(form["form"][FORM_ACTION])
        backend_api = form["form"][FIELD_NAME]
        outputs = form["outputs"]
        fields = form["fields"]
        genie_type = form["form"][FIELD_TYPE].lower()
        yield create_class(
            class_name,
            fields,
            genie_type,
            form_predicate,
            form_action,
            backend_api,
            outputs,
        )


# Function to dynamically create a class based on a dictionary
def create_class(
    class_name,
    fields,
    genie_type,
    form_predicate,
    form_action,
    backend_api,
    outputs,
):
    """Create a class dynamically based on the provided parameters.

    Args:
        class_name (str): The name of the class to create.
        fields (list): A list of field dictionaries.
        genie_type (str): The type of the Genie class (worksheet, db, type).
        form_predicate (str): The predicate for the form.
        form_action (Action): The action associated with the form.
        backend_api (str): The backend API associated with the form.
        outputs (list): A list of output dictionaries.

    Returns:
        Tuple[str, type]: The type of the class and the class itself."""

    # Create a dictionary for class attributes
    class_dict = {}
    for field_dict in fields:
        # Here, you would handle custom field types or validations
        class_dict[field_dict["name"]] = GenieField(**field_dict)

    if genie_type == "worksheet":
        class_dict["predicate"] = form_predicate
        class_dict["outputs"] = [output["slottype"] for output in outputs]
        class_dict["actions"] = form_action
        class_dict["backend_api"] = backend_api
        return (genie_type, type(class_name, (GenieWorksheet,), class_dict))
    elif genie_type == "db":
        class_dict["outputs"] = [output["slottype"] for output in outputs]
        class_dict["actions"] = form_action
        return (genie_type, type(class_name, (GenieDB,), class_dict))
    elif genie_type == "type":
        class_dict["predicate"] = form_predicate
        class_dict["actions"] = form_action
        return (genie_type, type(class_name, (GenieType,), class_dict))


def create_enum_class(class_name, enums):
    """Create an Enum class dynamically

    Args:
        class_name (str): The name of the Enum class.
        enums (list): A list of enum values.

    Returns:
        Enum: The created Enum class."""

    enums = [e.strip() for e in enums if len(e.strip())]
    return Enum(convert_snake_to_camel_case(class_name), enums)


def convert_snake_to_camel_case(snake_str: str):
    """Convert a snake_case string to camelCase.

    Args:
        snake_str (str): The snake_case string to convert.

    Returns:
        str: The converted camelCase string.
    """
    components = snake_str.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


str_to_type = {
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "date": datetime.date,
    "time": datetime.time,
}


def gsheet_to_genie(
    gsheet_id,
    gsheet_range=gsheet_range_default,
):
    print("inside gsheet_to_genie in from_spreadsheet.py")
    """Convert Google Sheets data to Genie componenets that are used to create the agent

    Args:
        gsheet_id (str): The ID of the Google Sheet.
        gsheet_range (str): The range of cells to retrieve.

    Returns:
        Tuple[List[GenieWorksheet], List[GenieDB], List[GenieType]]: The lists of Genie components.
    """
    try:
        genie_worsheets = []
        genie_worsheets_names = {}
        genie_dbs = []
        genie_dbs_names = {}
        genie_types = []
        genie_types_names = {}
        for genie_type, cls in gsheet_to_classes(gsheet_id, gsheet_range):
            if genie_type == "worksheet":
                genie_worsheets.append(cls)
                genie_worsheets_names[cls.__name__] = cls
            elif genie_type == "db":
                genie_dbs.append(cls)
                genie_dbs_names[cls.__name__] = cls
            elif genie_type == "type":
                genie_types.append(cls)
                genie_types_names[cls.__name__] = cls

        for worksheet in genie_worsheets + genie_dbs + genie_types:
            for field in get_genie_fields_from_ws(worksheet):
                if isinstance(field.slottype, str):
                    if field.slottype in str_to_type:
                        field.slottype = str_to_type[field.slottype]
                    elif field.slottype == "confirm":
                        field.slottype = "confirm"
                    elif field.slottype == "Enum":
                        field.slottype = Enum(field.name, field.slottype[1])
                    elif field.slottype.startswith("List"):
                        if field.slottype[5:-1] in genie_types_names:
                            field.slottype = List[genie_types_names[field.slottype[5:-1]]]
                        elif field.slottype[5:-1] in genie_dbs_names:
                            field.slottype = List[genie_dbs_names[field.slottype[5:-1]]]
                        elif field.slottype[5:-1] in genie_worsheets_names:
                            field.slottype = List[
                                genie_worsheets_names[field.slottype[5:-1]]
                            ]
                        else:
                            if field.slottype[5:-1] in str_to_type:
                                field.slottype = List[str_to_type[field.slottype[5:-1]]]
                            else:
                                raise ValueError(f"Unknown type {field.slottype}")
                    elif field.slottype in genie_types_names:
                        field.slottype = genie_types_names[field.slottype]
                    elif field.slottype in genie_dbs_names:
                        field.slottype = genie_dbs_names[field.slottype]
                    elif field.slottype in genie_worsheets_names:
                        field.slottype = genie_worsheets_names[field.slottype]
                    else:
                        raise ValueError(f"Unknown type {field.slottype}")

        for ws in genie_dbs + genie_worsheets:
            for output in ws.outputs:
                if output in genie_worsheets_names:
                    ws.outputs[ws.outputs.index(output)] = genie_worsheets_names[output]
                elif output in genie_types_names:
                    ws.outputs[ws.outputs.index(output)] = genie_types_names[output]
                else:
                    raise ValueError(f"Unknown type {output}")

        return genie_worsheets, genie_dbs, genie_types
    except Exception as e:
        print(f"Error: {e}")
        return [], [], []
