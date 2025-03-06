"""Keyframe parsing and processing for ChronoSynth."""

import re
import abc
from typing import Dict, Any, Tuple, List, Union, Optional

# Import asteval only if needed for safe expression evaluation
try:
    from asteval import Interpreter
    HAVE_ASTEVAL = True
except ImportError:
    HAVE_ASTEVAL = False


class SafeEvaluator:
    """Safe expression evaluator using asteval if available, otherwise limited support."""
    
    def __init__(self):
        """Initialize the evaluator."""
        self._interpreter = None
        if HAVE_ASTEVAL:
            self._interpreter = Interpreter(
                use_numpy=False,
                minimal=True,
                max_time=0.1,  # Prevent long-running expressions
                no_print=True
            )
    
    def evaluate(self, expr: str, variables: Dict[str, Any] = None) -> Any:
        """
        Safely evaluate an expression.
        
        Args:
            expr: Expression to evaluate
            variables: Variables to use in evaluation
            
        Returns:
            Result of evaluation
        """
        if variables is None:
            variables = {}
            
        # If asteval is available, use it
        if self._interpreter:
            # Set variables in the evaluator's symbol table
            for name, value in variables.items():
                self._interpreter.symtable[name] = value
                
            # Evaluate the expression
            result = self._interpreter.eval(expr)
            
            # Check for errors
            if self._interpreter.error:
                error_msg = f"Error evaluating expression: {self._interpreter.error_msg}"
                self._interpreter.error = False
                raise ValueError(error_msg)
                
            return result
        
        # If asteval is not available, provide limited support
        # Only allow simple numeric expressions with basic operators
        # This is not fully safe but provides basic functionality
        allowed_chars = set("0123456789.+-*/()^ ")
        if not all(c in allowed_chars for c in expr):
            raise ValueError("Expression contains unsupported characters")
        
        # Replace variables with their values
        for name, value in variables.items():
            if isinstance(value, (int, float)):
                expr = expr.replace(name, str(value))
                
        # Use eval with limited scope
        try:
            # Warning: This is still not entirely safe, but we've restricted the input
            # Replace ^ with ** for Python exponentiation
            expr = expr.replace("^", "**")
            return eval(expr, {"__builtins__": {}})
        except Exception as e:
            raise ValueError(f"Error evaluating expression: {e}")


class BaseKeyframeParser(abc.ABC):
    """Abstract base class for keyframe parsers."""
    
    def __init__(self, field_config):
        """
        Initialize with field configurations.
        
        Args:
            field_config: FieldConfig instance or dict with field configurations
        """
        self.field_config = field_config
        self.evaluator = SafeEvaluator()
    
    @abc.abstractmethod
    def parse(self, keyframe_str: str, total_seconds: float) -> Tuple[float, str, Any, Dict[str, Any], List[Tuple[str, str, float]]]:
        """
        Parse a keyframe string and return components.
        
        Args:
            keyframe_str: Keyframe expression string
            total_seconds: Total duration in seconds
            
        Returns:
            tuple: (time, field, value, options, relationships)
        """
        pass
    
    def _parse_time(self, time_part: str, total_seconds: float) -> float:
        """
        Parse time expression into seconds.
        
        Supports formats:
        - "end" => end of timeline
        - ".5" => fraction of total time
        - "30s" => 30 seconds
        - "5m" => 5 minutes
        - "2h" => 2 hours
        - "1h30m" => 1 hour and 30 minutes
        - "1:30" => 1 hour and 30 minutes
        - "1:30:45" => 1 hour, 30 minutes, and 45 seconds
        - "30" => 30 seconds (bare number)
        
        Args:
            time_part: Time part of keyframe string
            total_seconds: Total duration in seconds
            
        Returns:
            Time in seconds
        """
        if time_part == "end":
            # Use slightly before the end to ensure there's room for interpolation
            return total_seconds - 0.1
        elif time_part.startswith("."):
            try:
                fraction = float(time_part)
                return total_seconds * fraction
            except ValueError:
                raise ValueError(f"Invalid fraction time format: {time_part}")
        elif ":" in time_part:
            # Handle HH:MM or HH:MM:SS format
            try:
                parts = time_part.split(":")
                if len(parts) == 2:
                    # HH:MM format
                    hours, minutes = map(float, parts)
                    return (hours * 60 + minutes) * 60
                elif len(parts) == 3:
                    # HH:MM:SS format
                    hours, minutes, seconds = map(float, parts)
                    return hours * 3600 + minutes * 60 + seconds
                else:
                    raise ValueError(f"Invalid time format with colons: {time_part}")
            except ValueError:
                raise ValueError(f"Invalid time format with colons: {time_part}")
        elif "h" in time_part:
            # Handle combined formats like 1h30m, 1h30m45s, 4h20m, etc.
            try:
                h_parts = time_part.split("h")
                hours = float(h_parts[0])
                
                # Process the part after 'h'
                minutes = 0
                seconds = 0
                
                # Check if there's a minutes part
                if "m" in h_parts[1]:
                    m_parts = h_parts[1].split("m")
                    if m_parts[0]:  # Non-empty minutes part
                        minutes = float(m_parts[0])
                    
                    # Check if there's a seconds part
                    if len(m_parts) > 1 and "s" in m_parts[1]:
                        s_parts = m_parts[1].split("s")
                        if s_parts[0]:  # Non-empty seconds part
                            seconds = float(s_parts[0])
                # Just seconds after hours
                elif "s" in h_parts[1]:
                    s_parts = h_parts[1].split("s")
                    if s_parts[0]:  # Non-empty seconds part
                        seconds = float(s_parts[0])
                # Just a number after hours (assume minutes)
                elif h_parts[1]:
                    minutes = float(h_parts[1])
                
                return hours * 3600 + minutes * 60 + seconds
            except (ValueError, IndexError):
                raise ValueError(f"Invalid combined time format: {time_part}")
        elif time_part.endswith("m"):
            try:
                minutes = float(time_part[:-1])
                return minutes * 60
            except ValueError:
                raise ValueError(f"Invalid minute time format: {time_part}")
        elif time_part.endswith("s"):
            try:
                seconds = float(time_part[:-1])
                return float(seconds)
            except ValueError:
                raise ValueError(f"Invalid second time format: {time_part}")
        elif time_part.endswith("h"):
            try:
                hours = float(time_part[:-1])
                return hours * 3600
            except ValueError:
                raise ValueError(f"Invalid hour time format: {time_part}")
        else:
            try:
                return float(time_part)
            except ValueError:
                raise ValueError(f"Invalid time format: {time_part}")
    
    def resolve_value(self, field: str, value_expr: Any, current_value: float, normalize: bool, 
                     field_config: Dict[str, Dict[str, Any]]) -> float:
        """
        Resolve a value expression (absolute, relative, min/max).
        
        Args:
            field: Field name
            value_expr: Value expression (float or tuple)
            current_value: Current value of the field
            normalize: Whether to use normalization
            field_config: Field configuration dictionary
            
        Returns:
            Resolved value
        """
        if isinstance(value_expr, tuple) and len(value_expr) == 2:
            op, operand = value_expr
            
            if normalize:
                # Convert current_value to [0,1] range
                fmin = field_config[field]["min"]
                fmax = field_config[field]["max"]
                rng = fmax - fmin
                frac_current = (current_value - fmin) / rng if rng > 0 else 0
                
                # Apply operation in normalized space
                if op == '+':
                    frac_new = frac_current + operand
                elif op == '-':
                    frac_new = frac_current - operand
                elif op == '*':
                    frac_new = frac_current * operand
                elif op == '/':
                    frac_new = frac_current / operand if operand != 0 else frac_current
                elif op == '^':
                    frac_new = frac_current ** operand
                else:
                    frac_new = frac_current
                
                # Clamp to [0,1] and denormalize
                frac_new = max(0.0, min(1.0, frac_new))
                return fmin + frac_new * rng
            else:
                # Apply operation directly
                if op == '+':
                    return current_value + operand
                elif op == '-':
                    return current_value - operand
                elif op == '*':
                    return current_value * operand
                elif op == '/':
                    return current_value / operand if operand != 0 else current_value
                elif op == '^':
                    return current_value ** operand
        
        # For direct values
        if normalize and isinstance(value_expr, (int, float)):
            # Interpret as fraction [0,1]
            fmin = field_config[field]["min"]
            fmax = field_config[field]["max"]
            frac_val = max(0.0, min(1.0, value_expr))
            return fmin + frac_val * (fmax - fmin)
        
        # Return as is (already a min/max value or absolute value)
        return value_expr


class ClassicKeyframeParser(BaseKeyframeParser):
    """Standard parser for keyframe expressions using field@time format."""
    
    def __init__(self, field_config):
        super().__init__(field_config)
        
    def parse(self, keyframe_str: str, total_seconds: float) -> Tuple[float, str, Any, Dict[str, Any], List[Tuple[str, str, float]]]:
        """
        Parse a keyframe string and return components.
        
        Format examples:
          - g60@30s       => GPU set to 60 at 30s (stays at 60 after)
          - c^2@.5        => CPU set to (cpu_current^2) at 50% of timeline
          - r-5@1m        => RAM usage reduced by 5 at 1 minute
          - g+10@20s~     => GPU usage +10 at 20s with 'smooth' transition
          - g~            => Set default transition for GPU to smooth
          - g50@55s^      => Pulse: GPU to 50 at 55s, then return to previous value
          - g50@55s^+10   => Pulse: GPU to 50 at 55s, then return to (previous+10)
          - g~^           => Set default transition for GPU to smooth and pulse
          - c50@45s(pow=2, n=0.5) => CPU=50 at 45s with pow interpolation
          - rmin@.8(c*0.75) => RAM at min at 80% timeline, also sets CPU=75% of that
        
        Args:
            keyframe_str: Keyframe expression string
            total_seconds: Total duration in seconds
            
        Returns:
            tuple: (time, field, value, options, relationships)
        """
        # Validate keyframe string
        if not keyframe_str:
            raise ValueError("Empty keyframe string")
        
        # Get field configuration as dict
        field_config = self.field_config.fields if hasattr(self.field_config, 'fields') else self.field_config
        shorthand_map = self.field_config.shorthand_map if hasattr(self.field_config, 'shorthand_map') else {
            config["shorthand"]: field_name for field_name, config in field_config.items()
        }
        
        # Extract field shorthand
        shorthand = keyframe_str[0]
        if shorthand not in shorthand_map:
            valid_shortcuts = ", ".join(shorthand_map.keys())
            raise ValueError(f"Keyframe must start with a valid shorthand: {valid_shortcuts}")
        
        field = shorthand_map[shorthand]
        
        # Remove field shorthand
        expr = keyframe_str[1:]
        
        # Extract optional parameters in parentheses
        options = {}
        relationships = []
        
        if "(" in expr and expr.endswith(")"):
            expr_parts = expr.split("(", 1)
            expr = expr_parts[0]
            params_str = expr_parts[1][:-1]  # Remove trailing ')'
            
            # Parse parameters and relationships
            self._parse_params(params_str, options, relationships, shorthand_map)
        
        # Check for transition symbols - we now support multiple
        transition_map = {"~": "smooth", "|": "step", "#": "pulse"}  # ^ is reserved for post-behavior
        post_behavior = None
        post_value = None
        
        # Process transition behaviors in the expression
        # We need to capture any behavior symbols that might be present
        # IMPORTANT: These behaviors will be processed after we split the value and time
        # However, we still need to collect them here to remove them from the expression
        behavior_symbols = []
        behavior_modifiers = {}
        
        # First, look for ^ in the entire expression
        if "^" in expr:
            post_behavior = "return"
            behavior_symbols.append("^")
            
            # Check for modifiers after ^ like ^+10 or ^-5
            # This regex will find patterns like ^+10 or ^-5
            modifier_match = re.search(r"\^([\+\-\*\/])(\d+(\.\d+)?)", expr)
            if modifier_match:
                op = modifier_match.group(1)
                val = float(modifier_match.group(2))
                post_value = (op, val)
                # Remove the modifier from the expression
                expr = expr.replace(modifier_match.group(0), "^")
            else:
                # No specific modifier, just return to previous value
                post_value = None
        
        # Look for transition symbols in the entire expression
        for symbol, transition_type in transition_map.items():
            if symbol in expr:
                options["movement_type"] = transition_type
                behavior_symbols.append(symbol)
                
        # Now remove these symbols from the expression if they're not part of values
        # Be careful to only remove them when they're at the end of a segment
        # This handles cases like c80@10s^ or c20@30s~
        for symbol in behavior_symbols:
            expr = expr.replace("@" + symbol, "@")  # Handle symbol right after @
            
            # Replace a sequence like "@10s^" with "@10s"
            segments = expr.split("@")
            if len(segments) > 1:
                for i in range(1, len(segments)):
                    if symbol in segments[i]:
                        segments[i] = segments[i].replace(symbol, "")
                expr = "@".join(segments)
                
        # Store post-keyframe behavior
        if post_behavior:
            options["post_behavior"] = post_behavior
            if post_value:
                options["post_value"] = post_value
        
        # Split into value and time parts
        if "@" not in expr:
            # This could be a default setting keyframe (like g~ or g^)
            if not expr:
                # Handle the case of just a field shorthand (e.g., "g")
                time_val = None
                value = None
            else:
                # Handle setting default transition (e.g., "g~")
                time_val = None
                value = None
            
            return time_val, field, value, options, relationships
        else:
            # Normal keyframe with time
            value_part, time_part = expr.split("@", 1)
            
            # Parse value
            value = self._parse_value(value_part, field, field_config)
            
            # Parse time
            time_val = self._parse_time(time_part, total_seconds)
        
        return time_val, field, value, options, relationships
    
    def _parse_params(self, params_str: str, options: Dict[str, Any], 
                     relationships: List[Tuple[str, str, float]], shorthand_map: Dict[str, str]) -> None:
        """
        Parse parameters and relationships from the parentheses part.
        
        Args:
            params_str: Parameters string
            options: Options dictionary to update
            relationships: Relationships list to update
            shorthand_map: Map of shorthands to field names
        """
        for param in params_str.split(","):
            param = param.strip()
            
            if not param:
                continue
            
            # Check if it's a key=value pair
            if "=" in param:
                key, value = param.split("=", 1)
                key = key.strip()
                value = value.strip()
                
                # Handle special parameters
                if key in ["pow", "sin"]:
                    options["movement_type"] = key
                    if key == "pow":
                        options["pow"] = float(value)
                elif key == "n":
                    options["noise"] = float(value)
                else:
                    options[key] = value
            else:
                # Check if it's a relationship expression (e.g., "c*0.75")
                rel_match = re.match(r"([a-zA-Z])([\*\+\-\/\^])([\d\.]+)", param)
                
                if rel_match:
                    rel_field_short = rel_match.group(1)
                    rel_op = rel_match.group(2)
                    rel_val = float(rel_match.group(3))
                    
                    if rel_field_short in shorthand_map:
                        rel_field = shorthand_map[rel_field_short]
                        relationships.append((rel_field, rel_op, rel_val))
                elif param.lower() == "sin":
                    options["movement_type"] = "sin"
    
    def _parse_value(self, value_part: str, field: str, field_config: Dict[str, Dict[str, Any]]) -> Union[float, Tuple[str, float]]:
        """
        Parse the value part of a keyframe.
        
        Args:
            value_part: Value part of keyframe string
            field: Field name
            field_config: Field configuration dictionary
            
        Returns:
            Float or tuple (for relative values)
        """
        if value_part in ["min", "max"]:
            return field_config[field]["min" if value_part == "min" else "max"]
        elif value_part and value_part[0] in ["+", "-", "*", "/", "^"]:
            # Relative value - will be resolved later
            op = value_part[0]
            operand = float(value_part[1:])
            return (op, operand)
        else:
            # Absolute value or expression
            try:
                # Try as simple float first
                return float(value_part)
            except ValueError:
                # If it contains operators, try to evaluate as an expression
                try:
                    # This is where we would use the safe evaluator
                    result = self.evaluator.evaluate(value_part)
                    return float(result)
                except Exception as e:
                    raise ValueError(f"Invalid value expression: {value_part}, {e}")


class AtSignKeyframeParser(BaseKeyframeParser):
    """Parser for keyframe expressions using @time;field1value;field2value format."""
    
    def __init__(self, field_config):
        super().__init__(field_config)
    
    def parse(self, keyframe_str: str, total_seconds: float) -> Tuple[float, str, Any, Dict[str, Any], List[Tuple[str, str, float]]]:
        """
        Parse a keyframe string and return components.
        
        Format examples:
          - @20s;g80^      => GPU set to 80 at 20s with pulse behavior 
          - @30s;g60^10^+10 => GPU set to 60 at 30s, pulses to +10 then returns to +10
          - @30s;g50^75,55:5s => GPU set to 50 at 30s, spikes to 75 and returns to 55 over 5s
          - @20s;g70|      => GPU set to 70 at 20s with step transition
          - @10s;g~?*50:5s => GPU smooth transition to 50% of range over 5s
          - @30s;g-20;c-40 => GPU -20 and CPU -40 at 30s
          - @30s;g50^75,55:5s_2s;c~-40:3s_2s => Complex multi-field keyframe with hold times
          
        Args:
            keyframe_str: Keyframe expression string
            total_seconds: Total duration in seconds
            
        Returns:
            tuple: (time, field, value, options, relationships)
        """
        # Validate keyframe string
        if not keyframe_str or not keyframe_str.startswith('@'):
            raise ValueError("AtSign keyframe must start with @ symbol")
        
        # Get field configuration as dict
        field_config = self.field_config.fields if hasattr(self.field_config, 'fields') else self.field_config
        shorthand_map = self.field_config.shorthand_map if hasattr(self.field_config, 'shorthand_map') else {
            config["shorthand"]: field_name for field_name, config in field_config.items()
        }

        # Split the keyframe string into time and channel instructions
        parts = keyframe_str[1:].split(';', 1)  # Skip the @ symbol
        
        if len(parts) < 2:
            raise ValueError("AtSign keyframe must include time and at least one channel instruction")
        
        time_part = parts[0]
        channel_instructions = parts[1].split(';')
        
        # Parse the time
        time_val = self._parse_time(time_part, total_seconds)
        
        # We'll use only the first channel instruction for now and return it
        # In a real implementation, you'd need to parse all channels and manage them
        channel_instruction = channel_instructions[0]
        
        # Extract channel (field) shorthand
        shorthand = channel_instruction[0]
        if shorthand not in shorthand_map:
            valid_shortcuts = ", ".join(shorthand_map.keys())
            raise ValueError(f"Channel must start with a valid shorthand: {valid_shortcuts}")
        
        field = shorthand_map[shorthand]
        
        # Remove field shorthand
        channel_expr = channel_instruction[1:]
        
        # Initialize options and relationships
        options = {}
        relationships = []
        
        # Parse the type of modification
        value = None
        
        # Look for different modification patterns
        
        # Absolute value (number without prefix)
        if re.match(r'^\d+', channel_expr):
            value_match = re.match(r'^(\d+)', channel_expr)
            if value_match:
                value = float(value_match.group(1))
        
        # Step value (|)
        elif '|' in channel_expr:
            options["movement_type"] = "step"
            value_match = re.match(r'^(\d+)', channel_expr)
            if value_match:
                value = float(value_match.group(1))
        
        # Smooth transition (~)
        elif '~' in channel_expr:
            options["movement_type"] = "smooth"
            # Check for value after ~
            if re.search(r'~[-+]?\d+', channel_expr):
                value_match = re.search(r'~([-+]?\d+)', channel_expr)
                if value_match:
                    value = float(value_match.group(1))
            elif re.search(r'~\?', channel_expr):
                # Special case for expressions
                expr_match = re.search(r'~\?([\*\/\+\-]\d+)', channel_expr)
                if expr_match:
                    op = expr_match.group(1)[0]
                    operand = float(expr_match.group(1)[1:])
                    value = (op, operand)
        
        # Linear decrease/increase
        elif re.match(r'^[-+]\d+', channel_expr):
            options["movement_type"] = "linear"
            value_match = re.match(r'^([-+])(\d+)', channel_expr)
            if value_match:
                op = value_match.group(1)
                operand = float(value_match.group(2))
                value = (op, operand)
        
        # Spike pattern (^)
        elif '^' in channel_expr:
            options["post_behavior"] = "return"
            # Check for complex spike pattern like ^75,55:5s
            complex_spike = re.search(r'\^(\d+),(\d+):(\d+[ms])', channel_expr)
            if complex_spike:
                peak = float(complex_spike.group(1))
                return_val = float(complex_spike.group(2))
                duration = complex_spike.group(3)
                # In a real implementation, you'd store these as options
                options["spike_peak"] = peak
                options["return_value"] = return_val
                options["duration"] = duration
                
                # For simple demo, just return the first value
                value_match = re.match(r'^(\d+)', channel_expr)
                if value_match:
                    value = float(value_match.group(1))
            else:
                # Simple spike
                value_match = re.match(r'^(\d+)', channel_expr)
                if value_match:
                    value = float(value_match.group(1))
                
                # Check for post-return modification
                post_mod = re.search(r'\^\+(\d+)', channel_expr)
                if post_mod:
                    post_val = float(post_mod.group(1))
                    options["post_value"] = ('+', post_val)
        
        # Hold duration (_Ns)
        if '_' in channel_expr:
            hold_match = re.search(r'_(\d+[ms])', channel_expr)
            if hold_match:
                options["hold"] = hold_match.group(1)
        
        # Duration for transitions (:Ns)
        if ':' in channel_expr:
            duration_match = re.search(r':(\d+[ms])', channel_expr)
            if duration_match:
                options["duration"] = duration_match.group(1)
        
        # If we couldn't parse a value, use a reasonable default
        if value is None:
            value = field_config[field]["min"] + (field_config[field]["max"] - field_config[field]["min"]) / 2
        
        return time_val, field, value, options, relationships


class KeyframeParser:
    """Keyframe parser manager that auto-detects the appropriate parser."""
    
    def __init__(self, field_config):
        """
        Initialize with field configurations.
        
        Args:
            field_config: FieldConfig instance or dict with field configurations
        """
        self.field_config = field_config
        self.classic_parser = ClassicKeyframeParser(field_config)
        self.at_sign_parser = AtSignKeyframeParser(field_config)
    
    def parse(self, keyframe_str: str, total_seconds: float) -> Tuple[float, str, Any, Dict[str, Any], List[Tuple[str, str, float]]]:
        """
        Parse a keyframe string using the appropriate parser.
        
        Args:
            keyframe_str: Keyframe expression string
            total_seconds: Total duration in seconds
            
        Returns:
            tuple: (time, field, value, options, relationships)
        """
        # Auto-detect parser based on the first character
        if keyframe_str.startswith('@'):
            return self.at_sign_parser.parse(keyframe_str, total_seconds)
        else:
            return self.classic_parser.parse(keyframe_str, total_seconds)
    
    def resolve_value(self, field: str, value_expr: Any, current_value: float, normalize: bool, 
                     field_config: Dict[str, Dict[str, Any]]) -> float:
        """
        Resolve a value expression (absolute, relative, min/max).
        
        Args:
            field: Field name
            value_expr: Value expression (float or tuple)
            current_value: Current value of the field
            normalize: Whether to use normalization
            field_config: Field configuration dictionary
            
        Returns:
            Resolved value
        """
        # Both parsers use the same value resolution logic, so we can use either one
        return self.classic_parser.resolve_value(field, value_expr, current_value, normalize, field_config)
    
    def _parse_time(self, time_part: str, total_seconds: float) -> float:
        """
        Parse time expression into seconds.
        
        Args:
            time_part: Time part of keyframe string
            total_seconds: Total duration in seconds
            
        Returns:
            Time in seconds
        """
        # Both parsers use the same time parsing logic, so we can use either one
        return self.classic_parser._parse_time(time_part, total_seconds)