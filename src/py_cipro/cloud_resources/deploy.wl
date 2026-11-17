(* Evaluate this function with the endpoint path and a named secured authentication key. *)
Function[{endpointPath, keyName},
  Module[
    {release, digest, releaseURL, datasets, propertyKeys, ok, fail, fileDigest,
     archiveValid, memberPath, loadPackage, compute, probeDataset, serve,
     endpoint, archive, authorized, permissions, exists, scratch, zip, checked, deployed},

    release = "v1.0";
    digest = "39223db768893c958be776071bcbf86d0ef5692f92e1ab153ef1ce8d3440dd53";
    releaseURL = "https://github.com/JamesGray-Physics/CIPro/releases/download/v1.0/CIProPackage.zip";
    datasets = {"Cicy3", "Cicy4", "Cicy3Favour", "Cicy3Sym", "Cicy3FavourSym",
      "LBSStandardModels", "LBSStandardModels202", "delPezzo2"};
    propertyKeys = {"CIDim", "CY", "Euler"};

    ok[fields_] := Join[<|"ok" -> True, "release" -> release, "release_sha256" -> digest|>, fields];
    fail[code_] := <|"ok" -> False, "release" -> release, "release_sha256" -> digest, "error" -> code|>;
    fileDigest[file_] := Quiet[Check[FileHash[file, "SHA256", "HexString"], $Failed]];
    archiveValid[file_] := TrueQ[Quiet[Check[FileByteCount[file], $Failed]] === 27165392] &&
      fileDigest[file] === digest;
    memberPath[dir_, member_] := FileNameJoin[Prepend[StringSplit[member, "/"], dir]];

    loadPackage[file_, dir_, members_] := Module[
      {required, packagePath, text, prefix, relocation, headlessRules, runtimePath, loaded},
      required = Join[{"CIPro.m", "CIProAux/inst3.m", "CIProData/DataInfo.txt"}, members];
      (* Use one exact literal pattern per member. The pinned archive need not be fully expanded. *)
      If[!AllTrue[required, ListQ[Quiet[Check[ExtractArchive[file, dir, #], $Failed]]] &] ||
         !AllTrue[required, FileExistsQ[memberPath[dir, #]] &],
         Return["package_extract_failed"]];

      packagePath = memberPath[dir, "CIPro.m"];
      text = Quiet[Check[Import[packagePath, "Text", CharacterEncoding -> "UTF8"], $Failed]];
      prefix = "$UserBaseDirectory<>\"/Applications/";
      relocation = "CIPro`Private`$PyCIProApplicationRoot<>\"/";
      (* The Cloud API has no notebook display. Skip only its exact logo and help imports. *)
      headlessRules = {
        "Print[Style[Import[$UserBaseDirectory<>\"/Applications/CIProAux/Cinnamon.png\"], TextAlignment->Center,Magnification->0.75]];" -> "",
        "CIPro`MathInfo=Import[(\"ExamplePath\"/.Options[CIPro])<>\"manual/keyinfo.pdf\",ImageResolution->300];" -> "CIPro`MathInfo={};",
        "CIPro`MathInfoText=Import[(\"ExamplePath\"/.Options[CIPro])<>\"manual/keyinfo.pdf\",\"PagePlaintext\",ImageResolution->300];" -> "CIPro`MathInfoText={};",
        "CIPro`MathGeneralInfo=Import[(\"ExamplePath\"/.Options[CIPro])<>\"manual/generalinfo.pdf\",ImageResolution->300];" -> "CIPro`MathGeneralInfo={};",
        "CIPro`CIProManual=Import[(\"ExamplePath\"/.Options[CIPro])<>\"manual/CIPro_Manual.pdf\",ImageResolution->300];" -> "CIPro`CIProManual={};"
      };
      If[!StringQ[text] || StringCount[text, prefix] =!= 5 ||
         !AllTrue[headlessRules, StringCount[text, First[#]] === 1 &],
         Return["package_load_failed"]];
      text = StringReplace[StringReplace[text, headlessRules], prefix -> relocation];
      runtimePath = memberPath[dir, "CIProCloud.m"];
      If[Quiet[Check[Export[runtimePath, text, "Text", CharacterEncoding -> "UTF8"], $Failed]] === $Failed,
         Return["package_load_failed"]];

      CIPro`Private`$PyCIProApplicationRoot = dir;
      loaded = Quiet[Check[Get[runtimePath, CharacterEncoding -> "UTF8"], $Failed]];
      If[loaded === $Failed || !AssociationQ[CIPro`DataInfo] ||
         !AllTrue[datasets, KeyExistsQ[CIPro`DataInfo, #] &] ||
         !AssociationQ[CIPro`Private`CIProMod] ||
         !AllTrue[propertyKeys, KeyExistsQ[CIPro`Private`CIProMod, #] &] ||
         DownValues[CIPro`Data] === {} || DownValues[CIPro`CIProp] === {},
         Return["package_load_failed"]];
      Clear[CIPro`CILoad];
      True
    ];

    compute[recordNumber_, requested_] := Module[{row, matrix, ambient, values},
      row = Quiet[Check[CIPro`Data["Cicy3", recordNumber], $Failed]];
      If[!AssociationQ[row] || Lookup[row, "Num", None] =!= recordNumber,
         Return[fail["dataset_load_failed"]]];
      matrix = Lookup[row, "Conf", None];
      If[!MatrixQ[matrix, IntegerQ] || Length[matrix] == 0 || Length[First[matrix]] == 0 ||
         Min[Flatten[matrix]] < 0,
         Return[fail["dataset_schema_failed"]]];
      ambient = (Total[#] - 1 &) /@ matrix;
      If[Min[ambient] < 1 || Total[ambient] - Length[First[matrix]] =!= 3,
         Return[fail["dataset_schema_failed"]]];
      (* Give CIProp only the geometry, never archived values for the requested properties. *)
      values = Quiet[Check[CIPro`CIProp[<|"DimPs" -> ambient, "Conf" -> matrix|>, requested], $Failed]];
      If[!AssociationQ[values] || !AllTrue[requested,
          If[# === "CY", MemberQ[{True, False}, Lookup[values, #, None]],
            IntegerQ[Lookup[values, #, None]]] &],
         Return[fail["properties_failed"]]];
      ok[<|"properties" -> KeyTake[values, requested]|>]
    ];

    probeDataset[dir_, name_] := Module[{count, first, last, memberHash},
      memberHash = fileDigest[memberPath[dir, "CIProData/" <> name]];
      count = Quiet[Check[CIPro`Data[name, "Length"], $Failed]];
      (* A dump compatibility or load error must never pass through a stale or unevaluated value. *)
      If[!IntegerQ[count] || count < 1, Return[fail["dataset_load_failed"]]];
      first = Quiet[Check[CIPro`Data[name, 1], $Failed]];
      last = Quiet[Check[CIPro`Data[name, count], $Failed]];
      If[!AssociationQ[first] || !AssociationQ[last] || !StringQ[memberHash],
         Return[fail["dataset_schema_failed"]]];
      ok[<|"dataset" -> name, "count" -> count, "member_sha256" -> memberHash|>]
    ];

    serve[storedArchive_, operation_, recordText_, requestedText_, dataset_] := Module[
      {dir, localZip, members, requested, recordNumber, loaded},
      Switch[operation,
        "health", members = {},
        "properties",
          If[!StringQ[recordText] || !StringMatchQ[recordText, RegularExpression["[0-9]{1,4}"]] ||
             !StringQ[requestedText] || StringLength[requestedText] > 15,
             Return[fail["invalid_request"]]];
          recordNumber = FromDigits[recordText];
          requested = StringSplit[requestedText, ","];
          If[!Between[recordNumber, {1, 7890}] || !Between[Length[requested], {1, 3}] ||
             StringRiffle[requested, ","] =!= requestedText || !DuplicateFreeQ[requested] ||
             !AllTrue[requested, MemberQ[propertyKeys, #] &],
             Return[fail["invalid_request"]]];
          members = {"CIProData/Cicy3"},
        "dataset",
          If[!MemberQ[datasets, dataset], Return[fail["invalid_request"]]];
          members = {"CIProData/" <> dataset},
        _, Return[fail["invalid_request"]]
      ];
      TimeConstrained[
        WithCleanup[
          dir = Quiet[Check[CreateDirectory[], $Failed]],
          Block[{$Output = {}},
            If[!StringQ[dir], Return[fail["scratch_unavailable"]]];
            localZip = memberPath[dir, "CIProPackage.zip"];
            If[Quiet[Check[CopyFile[storedArchive, localZip], $Failed]] === $Failed || !FileExistsQ[localZip],
               Return[fail["archive_unavailable"]]];
            If[!archiveValid[localZip], Return[fail["archive_integrity"]]];
            loaded = loadPackage[localZip, dir, members];
            If[loaded =!= True, Return[fail[loaded]]];
            Switch[operation,
              "health", ok[<|"kernel_version" -> $Version, "system_id" -> $SystemID,
                  "system_word_length" -> $SystemWordLength|>],
              "properties", compute[recordNumber, requested],
              "dataset", probeDataset[dir, dataset]
            ]
          ],
          If[StringQ[dir] && DirectoryQ[dir], Quiet[DeleteDirectory[dir, DeleteContents -> True]]]
        ], 85, fail["evaluation_timeout"]
      ]
    ];

    If[!TrueQ[$CloudEvaluation], Return[fail["cloud_identity_unavailable"]]];
    If[!StringQ[endpointPath] || StringLength[endpointPath] > 120 ||
       !StringMatchQ[endpointPath, RegularExpression["py-cipro/(?:[a-zA-Z0-9][a-zA-Z0-9._-]*/)*[a-zA-Z0-9][a-zA-Z0-9._-]*"]] ||
       !StringQ[keyName] || !StringMatchQ[keyName, RegularExpression["[a-zA-Z0-9][a-zA-Z0-9._-]{0,79}"]],
       Return[fail["invalid_request"]]];
    If[!MatchQ[Quiet[Check[SecuredAuthenticationKeys[keyName], $Failed]], _SecuredAuthenticationKey],
       Return[fail["endpoint_permissions_failed"]]];
    endpoint = CloudObject[endpointPath];
    archive = CloudObject[endpointPath <> ".CIProPackage-v1.0.zip"];
    exists = Quiet[Check[FileExistsQ[endpoint], $Failed]];
    If[exists === True, Return[fail["endpoint_exists"]]];
    If[exists =!= False, Return[fail["endpoint_deploy_failed"]]];

    checked = WithCleanup[
      scratch = Quiet[Check[CreateDirectory[], $Failed]],
      If[!StringQ[scratch], Return[fail["scratch_unavailable"]]];
      zip = memberPath[scratch, "CIProPackage.zip"];
      exists = Quiet[Check[FileExistsQ[archive], $Failed]];
      If[exists === True,
        (* Reuse only matching private storage left by an earlier attempt. *)
        If[!MemberQ[{"Private", {}}, Quiet[Check[Information[archive, "Permissions"], $Failed]]],
           Return[fail["archive_not_private"]]],
        If[exists =!= False, Return[fail["archive_store_failed"]]];
        If[!MatchQ[Quiet[Check[URLDownload[releaseURL, zip, TimeConstraint -> 45], $Failed]], _File],
           Return[fail["archive_download_failed"]]];
        If[!archiveValid[zip], Return[fail["archive_integrity"]]];
        If[!MatchQ[Block[{$Permissions = "Private"}, Quiet[Check[CopyFile[zip, archive], $Failed]]], _CloudObject],
           Return[fail["archive_store_failed"]]];
      ];
      zip = memberPath[scratch, "stored-CIProPackage.zip"];
      If[Quiet[Check[CopyFile[archive, zip], $Failed]] === $Failed || !FileExistsQ[zip],
         Return[fail["archive_store_failed"]]];
      archiveValid[zip],
      If[StringQ[scratch] && DirectoryQ[scratch], Quiet[DeleteDirectory[scratch, DeleteContents -> True]]]
    ];
    If[AssociationQ[checked], Return[checked]];
    If[checked =!= True, Return[fail["archive_integrity"]]];

    deployed = With[{stored = archive}, Quiet[Check[
      CloudDeploy[
        APIFunction[{
          "operation" -> "String" -> "health", "record_id" -> "String" -> "",
          "properties" -> "String" -> "", "dataset" -> "String" -> ""
        }, Function[params, serve[stored, params["operation"], params["record_id"],
            params["properties"], params["dataset"]]], "RawJSON"],
        endpoint, Permissions -> "Private", IncludeDefinitions -> True
      ], $Failed]]];
    If[!MatchQ[deployed, _CloudObject], Return[fail["endpoint_deploy_failed"]]];
    authorized = Quiet[Check[SetPermissions[deployed,
        SecuredAuthenticationKeys[keyName] -> {"Read", "Execute"}], $Failed]];
    If[authorized === $Failed || FailureQ[authorized] || !FreeQ[authorized, _SetPermissions],
       Return[fail["endpoint_permissions_failed"]]];
    permissions = Quiet[Check[Information[deployed, "Permissions"], $Failed]];
    If[permissions === $Failed || FailureQ[permissions] ||
       !FreeQ[permissions, "Public" | "Authenticated" | _Information],
       Return[fail["endpoint_permissions_failed"]]];
    ok[<|"endpoint_path" -> endpointPath|>]
  ]
]
