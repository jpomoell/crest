# This file is part of CREST.
#
# Copyright 2025 CREST developers
#
# Use of this source code is governed by a BSD-style license 
# that can be found in the LICENSE.md file.

"""Dynamic accordion widgets
"""

import solara
from .panel import Panel


@solara.component
def ModelDynamicAccordion(items, type_map, model_date, model_time):
    
    keys = list(type_map.keys())
    
    # Type selection state
    type_choice = solara.use_reactive(keys[0])

    # Key name selection state
    key_choice, set_key_choice = solara.use_state("")
    
    pending_remove_key = solara.use_reactive(None)

    def add_item(key_name, type_name):
        """Adds a new item with (key, value) = (key_name, T) with T the 
        type associated with type_name
        """

        # Create new model entry
        new_item = type_map[type_name](model_date, model_time)

        if len(key_name) > 0:
            set_key_choice("")

            # Create updated dict
            items.set(dict(items.value, **{key_name: new_item}))


    def remove_item(key_name):
        """Remove the item associated with key_name
        """
        items.set({k: v for k, v in items.value.items() if k != key_name})
    
    
    with solara.Column(gap="5px", style={'padding' : '0px'}):
                
        with solara.Row(margin=0, gap="15px", justify="space-around"):
        
            # Sets the string that assoicated with the type 
            solara.Select(
                label="Model type",
                values=keys,
                value=type_choice,
            )

            # The name of the item
            with solara.Tooltip(f"Name that identifies this specific model"):
                solara.InputText("Name",
                                 value=key_choice,
                                 continuous_update=True,                                 
                                 on_value=set_key_choice,
                                 error=False if key_choice not in items.value.keys() else "Provide a distinct name for each model",
                                )
                                
            with solara.Tooltip(f"Add a new model of type {type_choice.value}"):
                solara.Button(
                    label="", 
                    icon_name="add",
                    on_click=lambda k=key_choice, t=type_choice.value: add_item(k, t),
                    color="blue",
                    style={"marginTop": "14px"}
                )
        
        # Build the accordion-like container structure by looping
        # through the dict
        for idx, (item_key, item) in enumerate(items.value.items()):            
            with solara.Column(style={'padding' : '0px', 'width' : '100%'}):
                with Panel(title=f"{item_key}", 
                           expand=True, 
                           header_style_="width:100%; font-color: rgba(0, 0, 0, 0.26); padding:0px", 
                           content_style_="width:100%; padding:0px; margin:0px"):
                    with solara.Column(style={'padding':'0px', 'width':'100%'}):
                        
                        solara.Column(children=[item.ui()], style={'padding':'0px', 'width':'100%'})
                        
                        with solara.Row(style={'padding':'0px', "width":"100%"}, justify='space-between'):
                            
                            solara.Button("Record",
                                          icon_name="mdi-file-edit",
                                          text=True,
                                          on_click=lambda _item=item: _item.record_parameters(),
                                          style={"font-size": "0.8rem"}
                                          )
                            
                            solara.Button("Remove model",
                                          icon_name="mdi-trash-can-outline", 
                                          text=True,
                                          on_click=lambda key=item_key: (
                                              pending_remove_key.set(key),
                                              ),
                                          style={"font-size": "0.8rem"}
                                          )
                            
    solara.lab.ConfirmationDialog(
        pending_remove_key.value is not None,
        title=f"Remove model {pending_remove_key.value}",
        content=(
            f"Are you sure you want to remove model "
            f"'{pending_remove_key.value}'? "
            "All data associated with the model will be lost."
        ),
        on_ok=lambda: (
            remove_item(pending_remove_key.value),
            pending_remove_key.set(None),            
        ),
        on_cancel=lambda: (
            pending_remove_key.set(None),            
            )
        )


@solara.component
def DataSourceDynamicAccordion(items, type_map):
    """A container for named items
    type_map : {nameA : clsA, nameB : clsB}
    """
    
    keys = list(type_map.keys())
    types = list(type_map.values())
    
    # Type selection state
    type_choice = solara.use_reactive(keys[0])
    #type_choice, set_type_choice = solara.use_state(keys[0])

    # Key name selection state
    #key_choice, set_key_choice = solara.use_state("")
    
    
    confirm_remove_item = solara.use_reactive(False)


    num_added_values = solara.use_reactive(0)


    def add_item(key_name, type_name):
        """Adds a new item with (key, value) = (key_name, T) with T the 
        type associated with type_name
        """

        # Create new entry
        new_item = type_map[type_name]()

        if len(key_name) > 0:
            #set_key_choice("")
            num_added_values.set(num_added_values.value + 1)

            # Create updated dict
            items.set(dict(items.value, **{key_name: new_item}))


    def remove_item(key_name):
        """Remove the item associated with key_name
        """
        items.set({k: v for k, v in items.value.items() if k != key_name})
    
    
    
    with solara.Column(gap="5px", style={'padding' : '0px'}):
        
        #solara.Markdown("*Add a data source*")


        with solara.Row(margin=0, gap="15px", justify="space-around"):
        
            # Sets the string that assoicated with the type
            with solara.Tooltip("Select the source of the data to be added"):
                solara.Select(
                    label="Data provider",
                    values=keys,
                    value=type_choice,
                    #on_value=lambda: type_choice.set,
                    #style={"min-width": "50px"},
                )

            # The name of the item
            #with solara.Tooltip("Name that identifies this model"):
            #    solara.InputText("Name",
            #                    value=key_choice,
            #                    continuous_update=True,
            #                    on_value=set_key_choice,
            #                    error=False if key_choice not in items.value.keys() else "Provide a distinct name for each item",
            #                    )
                                
            with solara.Tooltip("Add new item"):
                solara.Button(
                    label="add", 
                    icon_name="add",
                    on_click=lambda k=f"data-source-{num_added_values.value}", t=type_choice.value: add_item(k, t),
                    color="blue",
                    style={"marginTop": "14px"}
                )
        
        #solara.Markdown("Data sources:")

        # Build the accordion-like container structure by looping
        # through the dict
        for idx, (item_key, item) in enumerate(items.value.items()):       
            with solara.Column(style={'padding' : '0px', 'width' : '100%'}):
                source_name = f"{idx}"
                source_name += (": (" + item.measurement.nickname + ")") if item.measurement is not None else ""
                with Panel(title=f"Data source {source_name}", expand=True, header_style_="font-color: rgba(0, 0, 0, 0.26); padding:8px"):
                    with solara.Card(margin=0, elevation=0, style={'padding':'0px'}, children=[item.ui()]):
                        with solara.CardActions():
                            with solara.Row(style={"width":"100%"}, justify='end'):
                                solara.Button("Remove data source", icon_name="mdi-trash-can-outline", text=True, on_click=lambda: confirm_remove_item.set(True))
                                solara.lab.ConfirmationDialog(confirm_remove_item,
                                                            title="Remove data source",
                                                            on_ok=lambda key=item_key: remove_item(key),
                                                            content=f"Are you sure you want to remove Data Source {source_name}?")
