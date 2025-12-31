# This file is part of CREST.
#
# Copyright 2025 CREST developers
#
# Use of this source code is governed by a BSD-style license 
# that can be found in the LICENSE.md file.

"""Expandable details component
"""

import solara


@solara.component
def Panel(title="Title", children=[], expand=False, header_style_=None, content_style_=None):

    expand, set_expand = solara.use_state_or_update(expand)

    def on_v_model(v_model):
        if v_model is None:
            set_expand(False)
        elif v_model == 0:
            set_expand(True)
        else:
            raise RuntimeError(f"v_model has odd value: {v_model}")

    with solara.alias.rv.ExpansionPanels(v_model=0 if expand else None, on_v_model=on_v_model) as main:
        with solara.alias.rv.ExpansionPanel(style_="padding: 0px"):
            solara.alias.rv.ExpansionPanelHeader(children=[title], style_=header_style_)
            solara.alias.rv.ExpansionPanelContent(children=children, style_=content_style_)
    
    return main