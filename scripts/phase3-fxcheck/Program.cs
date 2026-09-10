using Microsoft.PowerFx;
using Microsoft.PowerFx.Types;
using System.Text.Json;
System.Globalization.CultureInfo.CurrentCulture=System.Globalization.CultureInfo.InvariantCulture;
System.Globalization.CultureInfo.CurrentUICulture=System.Globalization.CultureInfo.InvariantCulture;
System.Runtime.Loader.AssemblyLoadContext.Default.Resolving += (context, name) => {
 var path=Path.Combine("C:/Users/ramaz/.dotnet/tools/.store/microsoft.powerapps.cli.tool/2.11.2/microsoft.powerapps.cli.tool/2.11.2/tools/net10.0/any",name.Name+".dll");
 return File.Exists(path)?context.LoadFromAssemblyPath(path):null;
};
var engine=new RecalcEngine(new PowerFxConfig { MaximumExpressionLength = 100000 });
using var doc=JsonDocument.Parse(File.ReadAllText(args.Length > 0 ? args[0] : "validation/phase3/fx-input.json"));
int failures=0, count=0;
foreach(var rule in doc.RootElement.GetProperty("rules").EnumerateArray()) {
 var result=engine.Parse(rule.GetProperty("formula").GetString(),new ParserOptions{AllowsSideEffects=true});
 count++;
 if(result.Errors.Any()){failures++;Console.WriteLine("PARSE FAIL "+rule.GetProperty("name")+": "+string.Join(";",result.Errors));}
}
Console.WriteLine($"Parsed {count} runtime formulas; failures={failures}");
foreach(var test in doc.RootElement.GetProperty("tests").EnumerateArray()) {
 try{
 var result=engine.Eval(test.GetProperty("formula").GetString());
 var actual=result is StringValue s?s.Value:result.ToString();
 var ok=actual==test.GetProperty("expected").GetString();
 if(!ok) failures++;
 Console.WriteLine($"{test.GetProperty("name")}: {(ok?"PASS":"FAIL")} ({actual})");
 }catch(Exception e){failures++;Console.WriteLine("FAIL "+test.GetProperty("name")+" "+e.Message);}
}
Environment.ExitCode=failures==0?0:1;

