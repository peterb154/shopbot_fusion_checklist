{
  "controller": {
    "default": {
      "head_info_part_id": "head",
      "max_block_processing_speed": 0,
      "max_normal_speed": 15240.0,
      "non_tcp_rapid_interpolation_mode": "Synchronized",
      "parts": {
        "X": {
          "coordinate": 0,
          "max_normal_speed": 15240.0,
          "max_rapid_speed": 45720.0,
          "preference": "negative",
          "reset": "never",
          "reversed": false,
          "tcp": false,
          "zero_position_offset": 0
        },
        "Y": {
          "coordinate": 1,
          "max_normal_speed": 15240.0,
          "max_rapid_speed": 45720.0,
          "preference": "negative",
          "reset": "never",
          "reversed": false,
          "tcp": false,
          "zero_position_offset": 0
        },
        "Z": {
          "coordinate": 2,
          "max_normal_speed": 9144.0,
          "max_rapid_speed": 9144.0,
          "preference": "negative",
          "reset": "never",
          "reversed": false,
          "tcp": false,
          "zero_position_offset": 0
        },
        "table": {
          "max_normal_speed": 0,
          "max_rapid_speed": 0,
          "preference": "negative",
          "reset": "never",
          "reversed": false,
          "tcp": false,
          "zero_position_offset": 0
        }
      },
      "table_part_id": "table",
      "tcp_rapid_interpolation_mode": "ToolTip"
    }
  },
  "general": {
    "capabilities": [
      "cutting",
      "milling"
    ],
    "minimumRevision": 45805,
    "model": "PRSalpha 96x48",
    "vendor": "ShopBot Tools",
    "description": "ShopBot PRSalpha 96x48 (MCC). Travel 96 x 48 x 6 in, origin bottom-left, positive envelope. Manual tool change."
  },
  "interactions": {
    "default": {
      "pairs": [
        {
          "setting": null,
          "solids": [
            {
              "id": "X",
              "type": "machine_part"
            },
            {
              "id": "Y",
              "type": "machine_part"
            }
          ]
        },
        {
          "setting": [
            "check_collisions"
          ],
          "solids": [
            {
              "id": "X",
              "type": "machine_part"
            },
            {
              "id": "table",
              "type": "machine_part"
            }
          ]
        },
        {
          "setting": null,
          "solids": [
            {
              "id": "X",
              "type": "machine_part"
            },
            {
              "id": "table",
              "type": "stock"
            }
          ]
        },
        {
          "setting": null,
          "solids": [
            {
              "id": "X",
              "type": "machine_part"
            },
            {
              "id": "table",
              "type": "fixture"
            }
          ]
        },
        {
          "setting": [
            "check_collisions"
          ],
          "solids": [
            {
              "id": "Z",
              "type": "machine_part"
            },
            {
              "id": "Y",
              "type": "machine_part"
            }
          ]
        },
        {
          "setting": [
            "check_collisions"
          ],
          "solids": [
            {
              "id": "Z",
              "type": "machine_part"
            },
            {
              "id": "table",
              "type": "machine_part"
            }
          ]
        },
        {
          "setting": [
            "check_collisions"
          ],
          "solids": [
            {
              "id": "Z",
              "type": "machine_part"
            },
            {
              "id": "table",
              "type": "stock"
            }
          ]
        },
        {
          "setting": [
            "check_collisions"
          ],
          "solids": [
            {
              "id": "Z",
              "type": "machine_part"
            },
            {
              "id": "table",
              "type": "fixture"
            }
          ]
        },
        {
          "setting": [
            "check_collisions"
          ],
          "solids": [
            {
              "id": "head",
              "type": "machine_part"
            },
            {
              "id": "Y",
              "type": "machine_part"
            }
          ]
        },
        {
          "setting": [
            "check_collisions"
          ],
          "solids": [
            {
              "id": "head",
              "type": "tool"
            },
            {
              "id": "Y",
              "type": "machine_part"
            }
          ]
        },
        {
          "setting": [
            "check_collisions"
          ],
          "solids": [
            {
              "id": "head",
              "type": "machine_part"
            },
            {
              "id": "table",
              "type": "machine_part"
            }
          ]
        },
        {
          "setting": [
            "check_collisions"
          ],
          "solids": [
            {
              "id": "head",
              "type": "machine_part"
            },
            {
              "id": "table",
              "type": "stock"
            }
          ]
        },
        {
          "setting": [
            "check_collisions"
          ],
          "solids": [
            {
              "id": "head",
              "type": "machine_part"
            },
            {
              "id": "table",
              "type": "fixture"
            }
          ]
        },
        {
          "setting": [
            "check_collisions"
          ],
          "solids": [
            {
              "id": "head",
              "type": "tool"
            },
            {
              "id": "table",
              "type": "machine_part"
            }
          ]
        },
        {
          "setting": [
            "check_collisions"
          ],
          "solids": [
            {
              "id": "head",
              "type": "tool"
            },
            {
              "id": "table",
              "type": "stock"
            }
          ]
        },
        {
          "setting": [
            "check_collisions"
          ],
          "solids": [
            {
              "id": "head",
              "type": "tool"
            },
            {
              "id": "table",
              "type": "fixture"
            }
          ]
        },
        {
          "setting": null,
          "solids": [
            {
              "id": "Y",
              "type": "machine_part"
            },
            {
              "id": "table",
              "type": "machine_part"
            }
          ]
        },
        {
          "setting": [
            "check_collisions"
          ],
          "solids": [
            {
              "id": "Y",
              "type": "machine_part"
            },
            {
              "id": "table",
              "type": "stock"
            }
          ]
        },
        {
          "setting": [
            "check_collisions"
          ],
          "solids": [
            {
              "id": "Y",
              "type": "machine_part"
            },
            {
              "id": "table",
              "type": "fixture"
            }
          ]
        },
        {
          "setting": [
            "check_collisions"
          ],
          "solids": [
            {
              "id": "X",
              "type": "machine_part"
            },
            {
              "id": "Z",
              "type": "machine_part"
            }
          ]
        },
        {
          "setting": null,
          "solids": [
            {
              "id": "X",
              "type": "machine_part"
            },
            {
              "id": "head",
              "type": "machine_part"
            }
          ]
        },
        {
          "setting": [
            "check_collisions"
          ],
          "solids": [
            {
              "id": "X",
              "type": "machine_part"
            },
            {
              "id": "head",
              "type": "tool"
            }
          ]
        },
        {
          "setting": null,
          "solids": [
            {
              "id": "Z",
              "type": "machine_part"
            },
            {
              "id": "head",
              "type": "machine_part"
            }
          ]
        },
        {
          "setting": null,
          "solids": [
            {
              "id": "Z",
              "type": "machine_part"
            },
            {
              "id": "head",
              "type": "tool"
            }
          ]
        },
        {
          "setting": null,
          "solids": [
            {
              "id": "X",
              "type": "machine_part"
            },
            {
              "id": "static_0",
              "type": "machine_part"
            }
          ]
        },
        {
          "setting": null,
          "solids": [
            {
              "id": "Z",
              "type": "machine_part"
            },
            {
              "id": "static_0",
              "type": "machine_part"
            }
          ]
        },
        {
          "setting": null,
          "solids": [
            {
              "id": "Y",
              "type": "machine_part"
            },
            {
              "id": "static_0",
              "type": "machine_part"
            }
          ]
        },
        {
          "setting": [
            "check_collisions"
          ],
          "solids": [
            {
              "id": "table",
              "type": "machine_part"
            },
            {
              "id": "static_0",
              "type": "machine_part"
            }
          ]
        },
        {
          "setting": [
            "check_collisions"
          ],
          "solids": [
            {
              "id": "table",
              "type": "stock"
            },
            {
              "id": "static_0",
              "type": "machine_part"
            }
          ]
        },
        {
          "setting": [
            "check_collisions"
          ],
          "solids": [
            {
              "id": "table",
              "type": "fixture"
            },
            {
              "id": "static_0",
              "type": "machine_part"
            }
          ]
        },
        {
          "setting": [
            "check_collisions"
          ],
          "solids": [
            {
              "id": "head",
              "type": "machine_part"
            },
            {
              "id": "static_0",
              "type": "machine_part"
            }
          ]
        },
        {
          "setting": [
            "check_collisions"
          ],
          "solids": [
            {
              "id": "head",
              "type": "tool"
            },
            {
              "id": "static_0",
              "type": "machine_part"
            }
          ]
        }
      ]
    }
  },
  "kinematics": {
    "default": {
      "conventions": {
        "rotation": "right-handed"
      },
      "parts": [
        {
          "display_name": "static_0",
          "id": "static_0",
          "type": "static",
          "parts": [
            {
              "attach_frame": {
                "point": [
                  0,
                  0,
                  0
                ],
                "x_direction": [
                  1,
                  0,
                  0
                ],
                "z_direction": [
                  0,
                  0,
                  1
                ]
              },
              "display_name": "table",
              "id": "table",
              "type": "table"
            }
          ]
        },
        {
          "control": "driven",
          "direction": [
            1,
            0,
            0
          ],
          "id": "X",
          "max": 2438.4,
          "min": 0,
          "name": "X",
          "parts": [
            {
              "control": "driven",
              "direction": [
                0,
                1,
                0
              ],
              "id": "Y",
              "name": "Y",
              "min": 0,
              "max": 1219.2,
              "step_size": 0.001,
              "type": "linear",
              "parts": [
                {
                  "control": "driven",
                  "direction": [
                    0,
                    0,
                    1
                  ],
                  "home": 152.4,
                  "id": "Z",
                  "max": 152.4,
                  "min": 0,
                  "name": "Z",
                  "parts": [
                    {
                      "attach_frame": {
                        "point": [
                          -21.3211,
                          188.9506,
                          116.2799
                        ],
                        "x_direction": [
                          1,
                          0,
                          0
                        ],
                        "z_direction": [
                          0,
                          0,
                          1
                        ]
                      },
                      "display_name": "head",
                      "id": "head",
                      "spindle": {
                        "max_speed": 18000,
                        "min_speed": 0,
                        "peak_torque": 0,
                        "peak_torque_speed": 0,
                        "power": 2.2
                      },
                      "tool_station": {
                        "coolants": [],
                        "max_tool_diameter": 50.8,
                        "max_tool_length": 0
                      },
                      "type": "head"
                    }
                  ],
                  "step_size": 0.001,
                  "type": "linear",
                  "value_as_modelled": 152.4
                }
              ]
            }
          ],
          "step_size": 0.001,
          "type": "linear"
        }
      ],
      "units": {
        "angle": "degrees",
        "length": "mm"
      }
    }
  },
  "machining": {
    "default": {
      "feedrate_ratio": 1,
      "tool_change_time": 60
    }
  },
  "post": {
    "default": {
      "path": "system://shopbot.cps"
    }
  },
  "tooling": {
    "default": {
      "has_tool_changer": false,
      "number_of_tools": 1,
      "supports_tool_preload": false
    }
  }
}