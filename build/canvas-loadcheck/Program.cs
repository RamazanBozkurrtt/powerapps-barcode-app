using Microsoft.PowerPlatform.Formulas.Tools;
using System.Diagnostics;
System.Runtime.Loader.AssemblyLoadContext.Default.Resolving += (context, name) => {
 var path=Path.Combine("C:/Users/ramaz/.dotnet/tools/.store/microsoft.powerapps.cli.tool/2.11.2/microsoft.powerapps.cli.tool/2.11.2/tools/net10.0/any",name.Name+".dll");
 return File.Exists(path)?context.LoadFromAssemblyPath(path):null;
};
AppDomain.CurrentDomain.FirstChanceException += (_, e) => {
 if(true) { Console.WriteLine(e.Exception.GetType()+": "+e.Exception.Message);
  foreach(var frame in new StackTrace(e.Exception,true).GetFrames())
   Console.WriteLine(frame.GetMethod()+" IL:"+frame.GetILOffset());
 }
};
try { var (doc, errors)=CanvasDocument.LoadFromMsapp(Path.GetFullPath(args[0]));Console.WriteLine("LOADED="+(doc!=null)+" ERRORS="+errors.HasErrors); }
catch(Exception e){ Console.WriteLine(e); Environment.ExitCode=1; }
