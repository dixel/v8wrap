#:v8wrap:#
_simplify wrapping of your C functions to node.js_  
This is just a prototype version build for testing on libesmtp.  
This will be completely redisigned in future.  

### 1. Usage
        python codegen.py definition.json binding_source_name  
If everything all-right with your definition.json file, then `binding_source_name.h` and `bindign_source_name.cpp` will be created.

### 2. Json file format
    {  
       "include": ["what_to_include1.h", "what_to_include2.h"],  
       "data":  
       {  
            "internal":  
            {"data_typename":"100    DataTypeNameInJs", ...}  
       }  
       "functions":  
       {  
            "ordinary":  
            {  
                "FunctionNameJs":  
                {  
                    "ret": "ret_type",  
                    "name": "c_function_name",  
                    "args": {"arg_type":"0name", "arg_type":"1another_name", "some_callback_type":"cb_name" ...}  
                }  
                "FunctionNameJs2":  
                {  
                    "ret": ...  
                    ...  
                    ...  
                }  
            }  
            "callback":  
            {  
                "cb_name":  
                {  
                    "ret": "ret_type",  
                    "name": "JavaScriptName",  
                    "args": {"0type_name":"0param", "1type_name":"1param_next"}  
                }  
            }  
        }  
    }  
First field is "include" - this is just a list of all additional files we want to include in our module.  
Second field is "data". There we describe some "internal" data we don't know how to implement in JavaScript.  
The format of the "internal" field should be as in the example: the key is the name of data type in C, second is the name which we want to see in JavaScript. First 6 signs are reserved for number of objects of this type we want to have.  
"functions" field describes some functions we want to implement.  
"ordinary" are the functions that make some action just once and don't block program. "arg" field name of the function should always be prefixed with argument number.  
If argument is a callback function, than it's name should be listed in "callback" field (for example, "cb_name").  
A callback functions are described in "callback" field.  
Carefully: this script will not write the hole code which describe callbacks for you!  
Field name should be the c implementation name of your callback. "name" field of callback is the name of V8<Function> which will be stored in memory.  
Watch libesmtp.h, codegen.json for real example and run python codegen.py without parameters to see a real result.  
