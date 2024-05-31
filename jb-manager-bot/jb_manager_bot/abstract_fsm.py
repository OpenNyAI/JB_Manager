"""Module to define the abstract FSM class.
"""

from abc import ABC
from typing import Any, Dict, List, Set
from transitions import Machine
from jb_manager_bot.data_models import (
    FSMOutput,
    MessageData,
    MessageType,
    OptionsListType,
)
from jb_manager_bot.data_models import Status
from jb_manager_bot.parsers import Parser
import re
from datetime import datetime

class AbstractFSM(ABC):
    """Abstraction of the FSM class.
    Each use case will have its own FSM class.
    The FSM class will be used to define the states and transitions.
    """

    states: List[str] = []
    transitions: List[Dict[str, str]] = []
    conditions: Set[str] = set()
    output_variables: Set[str] = set()
    RUN_TOKEN = "RUNNING"

    def __init__(self, send_message: callable):
        """
        Initialize the FSM with a callback function.
        """
        self.send_message = send_message
        self.state = None
        self.status = Status.MOVE_FORWARD
        self.variables = {}
        self.outputs = {}
        self.plugins = self.plugins if hasattr(self, "plugins") else {}
        transitions = list(
            sorted(
                self.transitions,
                key=lambda x: (x.get("source"), x.get("conditions", "")),
                reverse=True,
            )
        )
        Machine(
            model=self,
            states=list(self.states),
            transitions=transitions,
            initial="zero",
        )

        self.__input__ = None
        self.__callback__ = None
        self.check_sanity()

    def initialise(self, **kwargs):
        """Method to initialise the FSM config."""
        for key, value in kwargs.items():
            self.variables[key] = value

    @property
    def current_input(self):
        """Property to get the current input."""
        return self.__input__

    @property
    def current_callback(self):
        """Property to get the current callback value."""
        return self.__callback__

    def run(self):
        """Method to start the FSM."""
        if self.status == Status.WAIT_FOR_PLUGIN:
            current_state = self.state
            state_method_name = f"on_enter_{current_state}"
            if hasattr(self, state_method_name):
                state_method = getattr(self, state_method_name)
                state_method()
        while self.status == Status.MOVE_FORWARD:
            self.next()
            self.reset_inputs()
        if self.status == Status.END:
            return self.outputs
        else:
            return self.RUN_TOKEN

    def submit_input(self, fsm_input: str):
        """Method to submit input to the FSM."""
        if fsm_input is not None:
            self.__input__ = fsm_input
            if self.status == Status.WAIT_FOR_USER_INPUT:
                self.status = Status.MOVE_FORWARD

    def submit_callback(self, fsm_callback: str):
        """Method to submit callback input to the FSM."""
        if fsm_callback is not None:
            self.__callback__ = fsm_callback
            if self.status == Status.WAIT_FOR_CALLBACK:
                self.status = Status.MOVE_FORWARD

    def reset_inputs(self):
        """Method to reset the inputs."""
        self.__input__ = None
        self.__callback__ = None

    def run_plugin(self, plugin: str, **kwargs):
        """Method to run a plugin."""
        plugin_obj: AbstractFSM = self.plugins.get(plugin)
        if not plugin_obj:
            raise ValueError(f"No such plugin found: {plugin}")
        if plugin_obj.state == "zero":
            plugin_obj.initialise(**kwargs)
        else:
            plugin_obj.submit_callback(self.current_callback)
            plugin_obj.submit_input(self.current_input)
        if (x := plugin_obj.run()) == plugin_obj.RUN_TOKEN:
            self.status = Status.WAIT_FOR_PLUGIN
            return self.RUN_TOKEN
        else:
            plugin_obj.reset()
            return x

    def _save_state(self):
        fsm_state = {
            "state": self.state,
            "status": self.status.value,
            "variables": self.variables,
        }
        plugin_states = {
            plugin: plugin_obj._save_state()
            for plugin, plugin_obj in self.plugins.items()
        }
        return {"main": fsm_state, "plugins": plugin_states}

    def _restore_state(self, state, status, variables, plugin_states):
        self.state = state
        self.status = Status(status)
        self.variables = variables
        for plugin, plugin_state in plugin_states.items():
            state = plugin_state["main"]["state"]
            status = Status(plugin_state["main"]["status"])
            variables = plugin_state["main"]["variables"]
            plugins = plugin_state["plugins"]
            self.plugins[plugin]._restore_state(state, status, variables, plugins)

    def reset(self):
        """Reset the FSM."""
        self.state = "zero"
        self.status = Status.MOVE_FORWARD
        self.variables = {}
        self.outputs = {}
        for plugin in self.plugins.values():
            plugin.reset()
        self.reset_inputs()

    def set_outputs(self):
        """Set the outputs of the FSM."""
        for key in self.output_variables:
            self.outputs[key] = self.variables.get(key, None)

    def on_enter_end(self):
        """Exit the FSM."""
        self.status = Status.WAIT_FOR_ME
        self.set_outputs()
        self.status = Status.END

    @classmethod
    def get_machine(
        cls,
        send_message: callable,
        credentials: Dict[str, Any] = None,
        state: str = None,
        status: Status = None,
        variables: Dict[str, Any] = None,
        plugin_states: Dict[str, Dict[str, Any]] = None,
    ):
        """Factory method to get FSM from state and variables."""
        if state is None:
            state = "zero"
        if variables is None:
            variables = {}
        if status is None:
            status = Status.MOVE_FORWARD
        if plugin_states is None:
            plugin_states = {}
        fsm = cls(send_message, credentials)
        fsm._restore_state(
            state=state, status=status, variables=variables, plugin_states=plugin_states
        )
        return fsm

    @classmethod
    def check_sanity(cls):
        """Check if the FSM is properly defined."""
        if len(cls.states) == 0:
            raise ValueError("No states defined")
        if len(cls.transitions) == 0:
            raise ValueError("No transitions defined")
        for condition in cls.conditions:
            if condition not in dir(cls):
                raise ValueError(f"Condition {condition} not defined in class {cls}")
        for state in cls.states:
            if not state == "zero" and f"on_enter_{state}" not in dir(cls):
                raise ValueError(
                    f"Implementation(On Enter Callback) of {state} not defined in class {cls}"
                )

    @classmethod
    def run_machine(
        cls,
        send_message: callable,
        user_input: str = None,
        callback_input: str = None,
        credentials: Dict[str, Any] = None,
        state: Dict[str, Any] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Method to run the FSM."""
        if state:
            fsm = cls.get_machine(
                send_message=send_message,
                credentials=credentials,
                state=state["main"]["state"],
                status=state["main"]["status"],
                variables=state["main"]["variables"],
                plugin_states=state["plugins"],
            )
        else:
            fsm = cls.get_machine(send_message=send_message, credentials=credentials)
        fsm.initialise(**kwargs)
        fsm.submit_callback(callback_input)
        fsm.submit_input(user_input)
        fsm.run()

        if fsm.status == Status.END:
            fsm.reset()

        return fsm._save_state()
    
    def create_select_lanaugage(self, state_name, destination, last_state="zero"):
        self._add_state(state_name)

        def on_enter_select_language(self):
            self.status = Status.WAIT_FOR_ME
            self.send_message(
                FSMOutput(
                    message_data=MessageData(
                        body="Please select your preferred language.\nबंधु से संपर्क करने के लिए धन्यवाद!\nकृपया अपनी भाषा चुनें।"
                    ),
                    type=MessageType.TEXT,
                    dialog="language",
                    dest="channel",
                )
            )
            self.status = Status.WAIT_FOR_USER_INPUT

        self._add_transition(last_state, state_name)
        on_enter_select_language.__name__ = f"on_enter_{state_name}"
        setattr(self.__class__, f"on_enter_{state_name}", on_enter_select_language)
        self._add_transition(state_name, destination)

    def _add_state(self, state_name):
        self.states.append(state_name)
    
    def _add_display_state(self, state_name):
        if not state_name.endswith("_display"):
            state_name = f"{state_name}_display"
        self.states.append(state_name)

    def _add_method(self, name, fn: callable):
        setattr(self.__class__, name, fn)

    def _add_input_states(self, state_name):
        self.states.extend(
            [
                f"{state_name}_display",
                f"{state_name}_input",
                f"{state_name}_logic",
                f"{state_name}_fail_display",
            ]
        )

    def _add_transition(self, source, destination, trigger="next", conditions=None):

        if conditions:
            self.transitions.append(
                {
                    "source": source,
                    "dest": destination,
                    "trigger": trigger,
                    "conditions": conditions,
                }
            )
        else:
            self.transitions.append(
                {"source": source, "dest": destination, "trigger": trigger}
            )
    def _on_enter_empty(self):
        self.status = Status.WAIT_FOR_ME
        self.status = Status.WAIT_FOR_USER_INPUT

    def _create_on_enter_input(self, fn_name):
        def dynamic_fn(self):
            return self._on_enter_empty()

        dynamic_fn.__name__ = fn_name
        setattr(self.__class__, fn_name, dynamic_fn)        
    
    def _on_enter_display(self, message, options=None, dialog=None, menu_selector=None, menu_title=None, media_url=None, dest_channel="out",):
            
        self.status = Status.WAIT_FOR_ME
        if options:
            type = MessageType.INTERACTIVE
            options = [
                OptionsListType(id=str(i + 1), title=option)
                for i, option in enumerate(options)
            ]
        elif media_url:
            type = MessageType.IMAGE
        else:
            type = MessageType.TEXT

        self.send_message(
                FSMOutput(
                    message_data=MessageData(body=message),
                    options_list=options,
                    type=type,
                    dest=dest_channel,
                    dialog=dialog,
                    menu_selector=menu_selector,
                    menu_title=menu_title,
                    media_url=media_url,
                )
            )
        self.status = Status.MOVE_FORWARD

    def _create_on_enter_display(
        self,
        fn_name,
        message,
        options=None,
        dialog=None,
        menu_selector=None,
        menu_title=None,
        media_url=None,
        dest_channel="out",
    ):
        
        def dynamic_fn(self):
            self._on_enter_display(
                message,
                options,
                dialog,
                menu_selector,
                menu_title,
                media_url,
                dest_channel,
            )
            

        dynamic_fn.__name__ = fn_name
        setattr(self.__class__, fn_name, dynamic_fn)
    
    def _on_enter_input_logic(self, write_var, options=None, message=None, validation=None):
        self.status = Status.WAIT_FOR_ME
        if options:
            task = f"The user provides a response to the {message}."
            options = [OptionsListType(id=str(i + 1), title=option) for i, option in enumerate(options)]
        else:
            task = f"This is the question being asked to the user: {message}. This is validation that the variable need to pass {validation}. Format and modify the user input into the format requied and if you could not be decide return None. Based on the user's input, return the output in json format: {{'result': <input>}}"
        result = Parser.parse_user_input(
                task,
                options,
                self.current_input,
                azure_endpoint=self.credentials["AZURE_OPENAI_API_ENDPOINT"],
                azure_openai_api_key=self.credentials["AZURE_OPENAI_API_KEY"],
                azure_openai_api_version=self.credentials["AZURE_OPENAI_API_VERSION"],
                openai_api_key=self.credentials["OPENAI_API_KEY"],
            )
        if options :
            result = result["id"]
            if result.isdigit():
                result = options[int(result) - 1].title
        else:
            result = result["result"]
        self.variables[write_var] = result
        
        self.status = Status.MOVE_FORWARD


    def _create_on_enter_input_logic_method(self, state_name, write_var, options, message, validation):
        def dynamic_fn(self):
            self._on_enter_input_logic(write_var, options, message, validation)
        dynamic_fn.__name__ = f"on_enter_{state_name}"
        setattr(self.__class__, f"on_enter_{state_name}", dynamic_fn)   
    
    def _create_state_with_empty_on_enter(self, state_name):
        self._add_state(state_name)
        
        def dynamic_fn(self):
            self.status = Status.WAIT_FOR_ME
            self.status = Status.MOVE_FORWARD
        dynamic_fn.__name__ = f"on_enter_{state_name}" 
        setattr(self.__class__, f"on_enter_{state_name}", dynamic_fn)     

    def create_display_task(
        self,
        source,
        dest,
        message,
        options=None,
        dialog=None,
        menu_selector=None,
        menu_title=None,
        media_url=None,
        dest_channel="out",
        format_variables=None,
    ):
        # if format_variables:
        #     write_variables = {k: self.__class__.variables[k] for k in format_variables}
        #     message = message.format(write_variables)
        self._add_display_state(source)
        self._add_transition(source, dest)
        self._create_on_enter_display(
            f"on_enter_{source}",
            message,
            options,
            dialog,
            menu_selector,
            menu_title,
            media_url,
            dest_channel,
        )

    def create_input_task(
        self,
        name,
        message,
        success_dest,
        is_valid=None,
        options=None,
        dialog=None,
        menu_selector=None,
        menu_title=None,
        media_url=None,
        fail_dest=None,
        write_var=None,
        validation_expression=None,
    ):
        
        self._add_input_states(name)
        self._add_transition(f"{name}_display", f"{name}_input")
        self._add_transition(f"{name}_input", f"{name}_logic")
        self._add_transition(f"{name}_logic", fail_dest)
        
        self._create_on_enter_display(
            f"on_enter_{name}_display",
            message,
            options,
            dialog,
            menu_selector,
            menu_title,
            media_url,
        )

        self._create_on_enter_input(f"on_enter_{name}_input")
        self._create_on_enter_input_logic_method(f"{name}_logic", write_var, options, message, validation_expression)
        self._create_is_valid_method(f"is_valid_{write_var}", validation_expression, write_var)
        self._add_transition(f"{name}_logic", success_dest, conditions=f"is_valid_{write_var}")


    def create_branching_task(self, source, transitions):
        self._create_state_with_empty_on_enter(source)
        
        for transition in transitions:
            condition = transition["condition"]
            if "expression" in transition:
                expression = transition["expression"]
                var = transition["variable"]
                self._create_is_valid_method(f"{condition}", expression, var)
            dest = transition["dest"]
            self._add_transition(source, dest, conditions=condition)
    
    
    def _on_enter_plugin(self, plugin, input_variables, output_variables, message=None):
        self.status = Status.WAIT_FOR_ME
        if message:
                self.send_message(
                    FSMOutput(
                        message_data=MessageData(body=message),
                        type=MessageType.TEXT,
                        dest="out",
                    )
                )
        
        plugin_input = {key: self.variables[value] for key, value in input_variables.items()}
        plugin_output = plugin(**plugin_input)

        for key, value in output_variables.items():
            self.variables[value] = plugin_output[key]

        self.status = Status.MOVE_FORWARD

        
    def create_plugin_task(self, source, message, plugin_fn, input_variables:Dict, output_variables:Dict, transitions:List[Dict]):
        self._add_state(source)
        def dynamic_fn(self):
            self._on_enter_plugin(plugin_fn, input_variables, output_variables, message)
        
        dynamic_fn.__name__ = f"on_enter_{source}"
        setattr(self.__class__, f"on_enter_{source}", dynamic_fn)

        for transition in transitions:
            condition = transition["condition"]
            condition_fn_name = f"is_error_code_{condition}"
            self._create_plugin_error_code_method(condition_fn_name, condition)
            dest = transition["dest"]
            self._add_transition(source, dest, conditions=condition_fn_name)
    
    def _create_is_valid_method(self, fn_name, expression, variable):
        def dynamic_fn(self):
            variable_name = variable
            condition = expression.replace(variable_name, f"{variable_name}")
            lambda_func = eval(f"lambda {variable_name}: {condition}")
            return self._validate_method(variable_name, lambda_func)
        
        dynamic_fn.__name__ = f"{fn_name}"
        setattr(self.__class__, dynamic_fn.__name__, dynamic_fn)

    def _validate_method(self, variable_name, lambda_func):
        value = self.variables.get(variable_name)
        return lambda_func(value)
    
    def _plugin_error_code_validation(self, error_code):
            return self.variables["error_code"] == error_code
    
    def _create_plugin_error_code_method(self, name, error_code):
        def dynamic_fn(self):
            return self._plugin_error_code_validation(error_code)
        dynamic_fn.__name__ = name
        setattr(self.__class__, name, dynamic_fn)
    

