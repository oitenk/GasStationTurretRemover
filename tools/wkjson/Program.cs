using WolvenKit.Common.Conversion;
using WolvenKit.RED4.Archive.IO;
using WolvenKit.RED4.Archive.CR2W;
using WolvenKit.RED4.Types;
using WolvenKit.RED4.CR2W.JSON;
// usage: wkjson read <game file> <out.json>
//        wkjson write <in.json> <game file>
//
// "read" accepts InvalidDefaultValue notices (a value written that equals the type's
// default), which 2.5 sectors contain; any other parsing problem stops it.
if (args[0] == "read")
{
    using var fs = File.OpenRead(args[1]);
    using var reader = new CR2WReader(fs);
    int notices = 0;
    reader.ParsingError += e => { if (e is InvalidDefaultValueEventArgs) { notices++; return true; } Console.WriteLine("parse error: " + e.GetType().Name); return false; };
    var status = reader.ReadFile(out var cr2w);
    if (status != EFileReadErrorCodes.NoError) { Console.WriteLine($"read failed: {status}"); return 1; }
    File.WriteAllText(args[2], RedJsonSerializer.Serialize(new RedFileDto(cr2w)));
    Console.WriteLine($"read ok ({notices} default-value notices)");
}
else
{
    var dto = RedJsonSerializer.Deserialize<RedFileDto>(File.ReadAllText(args[1]));
    if (dto?.Data == null) { Console.WriteLine("json did not deserialize"); return 1; }
    using var ms = new MemoryStream();
    using (var writer = new CR2WWriter(ms, System.Text.Encoding.UTF8, true)) writer.WriteFile(dto.Data);
    File.WriteAllBytes(args[2], ms.ToArray());
    Console.WriteLine($"wrote {ms.Length} bytes");
}
return 0;
