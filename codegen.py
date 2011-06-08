#!/usr/bin/env python
#! -*-coding: utf-8 -*-

import sys
import os
import re
import json 
class NodeModule():
    def __init__(self, filename, sourcename):
        try:
            self.base = json.loads("".join([i for i in file(filename, 'r')]))
        except ValueError:
            print("error parsing your json file")
        self.sourcename = sourcename
        self.header = file("%s.h" % (sourcename), 'w')
        self.source = file("%s.cc" % (sourcename), 'w')

    def WriteHeader(self): 
        #{{{1include/define
        self.header.write("#define V8STR String::AsciiValue\n")
        self.header.write("#include <node.h>\n")
        self.header.write("#include <stdio.h>\n")
        self.header.write("#include <string.h>\n")
        self.header.write("#include <node_events.h>\n")
        self.header.write("#include <pthread.h>\n")
        self.header.write("#include <limits.h>\n")
        self.header.write("#include <map>\n")
        for i in self.base['include']:
            self.header.write("#include <%s>\n" % i)
        self.header.write("using namespace v8;\n")
        #1}}}

        #{{{1 ordinary functions conversion
        ordinary = self.base['functions']['ordinary']
        for i in ordinary:
            self.header.write("//Ordinary function %s(...) - analogue of %s %s(%s)\n" % 
                    (i, ordinary[i]['ret'], ordinary[i]['name'], ", ".join(ordinary[i]['args'])))
            self.header.write("static Handle<Value> %s (const Arguments &args);\n" % (i))
        #1}}}
        
        #{{{1data implementation
        for i in self.base["data"]["internal"]:
            self.header.write("%s _%s[%s];\n" % (i, self.base["data"]["internal"][i][6:], self.base["data"]["internal"][i][0:6].strip()))
            #self.header.write("Persistent<Object> %s[%s];\n" % (self.base["data"]["internal"][i][6:], self.base["data"]["internal"][i][0:6].strip()))
            self.header.write("unsigned long int cnt_%s;\n" % (self.base["data"]["internal"][i][6:]))
        #1}}}

        #{{{1useful functions just for me
        self.header.write("int strip_id(Handle<Value> obj);\n")
        self.header.write("Handle<Function> strip_fun(Handle<Value> obj);\n")
        #1}}}

        #{{{1callbacks
        cbs = self.base["functions"]["callback"]
        for i in cbs:
            self.header.write("%s %s(%s);\n" % 
                    (cbs[i]["ret"], i, ", ".join(["%s %s" % (typ[1:], arg[1:]) for typ, arg in cbs[i]["args"].items()])))
            self.header.write("struct ev_async ev_%s;\n" % (i))
        #1}}}

        self.header.close()

    def WriteSource(self):
        self.source.write("#include \"%s.h\"\n" % (self.sourcename))

        #{{{1ordinary functions
        ordinary = self.base['functions']['ordinary']
        for i in ordinary:
            self.source.write("static Handle<Value> %s(const Arguments &args)\n{\n" % (i))
            self.source.write("    printf(\"DEBUG:: %s\\n\");\n" % (i))
            callargs = []
            callid = ""
            for arg in ordinary[i]["args"]:
                if arg in self.base['data']['internal']:
                    self.source.write("    unsigned long int %s = strip_id(args[%s]);\n" % 
                            ("id_" + arg, ordinary[i]["args"][arg][0]))
                    callargs.append("_%s[%s]" % (self.base['data']['internal'][arg][6:], "id_" + arg))
                if arg == "const char *":
                    self.source.write("    const char *%s = *(V8STR(args[%s]));\n" % 
                            (ordinary[i]["args"][arg][1:], ordinary[i]["args"][arg][0]))
                    callargs.append(ordinary[i]["args"][arg][1:])
                if arg == "int":
                    self.source.write("    int %s = args[%s]->Int32Value();\n" % 
                            (ordinary[i]["args"][arg][1:], ordinary[i]["args"][arg][0]))
                    callargs.append(ordinary[i]["args"][arg][1:])
                if ordinary[i]["args"][arg][1:] in self.base['functions']['callback']:
                    self.source.write("    Persistent<Function> CB = Persistent<Function>::New(strip_fun(args[%s]));\n" % (ordinary[i]["args"][arg][0]))
                    callargs.append(ordinary[i]["args"][arg][1:])
                    callargs.append("&CB")
            print callargs
            if ordinary[i]["ret"] in self.base['data']['internal']:
                nname = self.base['data']['internal'][ordinary[i]["ret"]][6:]
                print nname
                self.source.write("    cnt_%s++;\n" % (nname))
                self.source.write("    _%s[cnt_%s] = %s(%s);\n" % (nname, nname, ordinary[i]["name"], ", ".join(callargs)))
                self.source.write("    Local<Object> %s = Object::New();\n" % (nname))
                self.source.write("    %s->Set(String::New(\"%s_id\"), Integer::New(cnt_%s));\n" % (nname, nname, nname))
                self.source.write("    return %s;\n" % (nname))
            elif ordinary[i]["ret"] == "int":
                self.source.write("    return Integer::New(%s(%s));\n" % (ordinary[i]["name"], ", ".join(callargs)))

            self.source.write("}\n")
        #1}}}

        #{{{1 callbacks
        cbs = self.base["functions"]["callback"]
        for i in cbs:
            self.source.write("%s %s(%s)\n{\n" % 
                    (cbs[i]["ret"], i, ", ".join(["%s %s" % (typ[1:], cbs[i]["args"][typ][1:]) for typ in cbs[i]["args"]])))
            self.source.write("//CURRENTLY ONLY YOUR CODE HERE-------------------------------\n")
            self.source.write("}\n")
        #1}}}

        #{{{1 useful functions just for me
        self.source.write("""\
int strip_id(Handle<Value> obj)
{
    if(obj->IsObject())
    {
        Local<Object> object = Object::Cast(*obj);
        if (object->Has(String::New(\"objid\")))
            return object->Get(String::New(\"objid\"))->Int32Value();
        else
            return 0;
    }
    else
        return 0;
}\n""")
        self.source.write("""\
Handle<Function> strip_fun(Handle<Value> fun)
{
    if(fun->IsFunction())
    {
        Local<Function> fn = Function::Cast(*(fun));
        return fn;
    }
}\n""")
        #1}}}

        #{{{1 main module
        self.source.write("extern \"C\" void\ninit (Handle<Object> target)\n{\n")
        self.source.write("HandleScope scope;\n")
        for i in ordinary:
            self.source.write("    target->Set(String::NewSymbol(\"%s\"), FunctionTemplate::New(%s)->GetFunction());\n" % (i, i))
        self.source.write("}")
        #1}}}
        
        self.source.close()
        
if __name__ == '__main__':
    test = NodeModule("codegen.json", "binding")
    test.WriteHeader()
    test.WriteSource()