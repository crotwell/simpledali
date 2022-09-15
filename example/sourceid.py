import simpledali

chanSourceId = "FDSN:CO_JSC_00_H_H_Z"
chanNslc = "CO_JSC_00_HHZ"

sid = simpledali.FDSNSourceId.parse(chanSourceId)
print(sid)
sid2 = simpledali.FDSNSourceId.parseNslc(chanNslc, sep='_')
print(sid2)
sid3 = simpledali.FDSNSourceId.fromNslc("CO", "JSC", "00", "HHZ")
print(sid3)
print(sid == sid2)
print(sid == sid3)

print(sid.stationSourceId())
print(sid.stationSourceId() == sid2.stationSourceId())
print(sid.stationSourceId() == simpledali.FDSNSourceId.parse("FDSN:CO_JSC"))


print(sid.networkSourceId())
print(sid.networkSourceId() == sid2.networkSourceId())
print(sid.networkSourceId() == simpledali.FDSNSourceId.parse("FDSN:CO"))

print(simpledali.FDSNSourceId.createUnknown())
print(simpledali.FDSNSourceId.createUnknown(100))
print(simpledali.FDSNSourceId.createUnknown(1))
print(simpledali.FDSNSourceId.createUnknown(.01))

print(simpledali.nslcToStreamId("CO", "JSC", "00", "HHZ", "MSEED"))
print(simpledali.fdsnSourceIdToStreamId(sid, "MSEED"))
