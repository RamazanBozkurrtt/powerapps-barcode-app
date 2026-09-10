using Microsoft.PowerFx;
foreach(var t in new[]{typeof(PowerFxConfig),typeof(ParserOptions),typeof(RecalcEngine)}) foreach(var p in t.GetProperties()) System.Console.WriteLine(t.Name+" "+p);
