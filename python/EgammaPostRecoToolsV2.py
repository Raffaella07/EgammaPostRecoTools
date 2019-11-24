import FWCore.ParameterSet.Config as cms
import pkgutil

#define the default IDs to produce in VID
_defaultEleIDModules =  [ 'RecoEgamma.ElectronIdentification.Identification.heepElectronID_HEEPV70_cff',
                        'RecoEgamma.ElectronIdentification.Identification.cutBasedElectronID_Fall17_94X_V1_cff',
                        'RecoEgamma.ElectronIdentification.Identification.mvaElectronID_Fall17_noIso_V1_cff', 
                        'RecoEgamma.ElectronIdentification.Identification.mvaElectronID_Fall17_iso_V1_cff',
                        'RecoEgamma.ElectronIdentification.Identification.cutBasedElectronID_Summer16_80X_V1_cff',
                        'RecoEgamma.ElectronIdentification.Identification.mvaElectronID_Spring16_GeneralPurpose_V1_cff',
                        'RecoEgamma.ElectronIdentification.Identification.mvaElectronID_Spring16_HZZ_V1_cff',
                        ]
_defaultPhoIDModules =  [ 'RecoEgamma.PhotonIdentification.Identification.cutBasedPhotonID_Fall17_94X_V1_TrueVtx_cff',
                        #'RecoEgamma.PhotonIdentification.Identification.mvaPhotonID_Fall17_94X_V1_cff', 
                        'RecoEgamma.PhotonIdentification.Identification.mvaPhotonID_Fall17_94X_V1p1_cff', 
                        'RecoEgamma.PhotonIdentification.Identification.cutBasedPhotonID_Spring16_V2p2_cff',
                        'RecoEgamma.PhotonIdentification.Identification.mvaPhotonID_Spring16_nonTrig_V1_cff'
                        ]

#the new Fall17V2 modules are loaded as default if they exist in the release
#we do it this way as we can use the same script for all releases and people who
#dont want V2 can still use this script
_fall17V2PhoMVAIDModules = [
    'RecoEgamma.PhotonIdentification.Identification.mvaPhotonID_Fall17_94X_V2_cff'
    ]
_fall17V2PhoCutIDModules = [
    'RecoEgamma.PhotonIdentification.Identification.cutBasedPhotonID_Fall17_94X_V2_cff'
    ]
_fall17V2EleIDModules = [
    'RecoEgamma.ElectronIdentification.Identification.cutBasedElectronID_Fall17_94X_V2_cff',
    'RecoEgamma.ElectronIdentification.Identification.mvaElectronID_Fall17_noIso_V2_cff',
    'RecoEgamma.ElectronIdentification.Identification.mvaElectronID_Fall17_iso_V2_cff'
    ]

if pkgutil.find_loader(_fall17V2EleIDModules[0]) != None:
    _defaultEleIDModules.extend(_fall17V2EleIDModules)
else:
    print "EgammaPostRecoTools: Fall17V2 electron modules not found, running ID without them. If you want Fall17V2 IDs, please merge the approprate PR\n  94X:  git cms-merge-topic cms-egamma/EgammaID_949"

if pkgutil.find_loader(_fall17V2PhoMVAIDModules[0]) != None:
    _defaultPhoIDModules.extend(_fall17V2PhoMVAIDModules)
else:
    print "EgammaPostRecoTools: Fall17V2 MVA photon modules not found, running ID without them. If you want Fall17V2 MVA Photon IDs, please merge the approprate PR\n  94X:  git cms-merge-topic cms-egamma/EgammaID_949\n  102X: git cms-merge-topic cms-egamma/EgammaID_1023"

if pkgutil.find_loader(_fall17V2PhoCutIDModules[0]) != None:
    _defaultPhoIDModules.extend(_fall17V2PhoCutIDModules)
else:
    print "EgammaPostRecoTools: Fall17V2 cut based Photons ID modules not found, running ID without them. If you want Fall17V2 CutBased Photon IDs, please merge the approprate PR\n  94X:  git cms-merge-topic cms-egamma/EgammaID_949\n  102X: git cms-merge-topic cms-egamma/EgammaID_1023"

def _check_valid_era(era):
    valid_eras = ['2017-Nov17ReReco','2016-Legacy','2016-Feb17ReMiniAOD','2018-Prompt']
    if era not in valid_eras:
        raise RuntimeError('error, era {} not in list of allowed eras {}'.format(value,str(valid_eras)))
    return True


def _getEnergyCorrectionFile(era):
    _check_valid_era(era)
    if era=="2017-Nov17ReReco":
        return "EgammaAnalysis/ElectronTools/data/ScalesSmearings/Run2017_17Nov2017_v1_ele_unc"
    if era=="2016-Legacy":
        return "EgammaAnalysis/ElectronTools/data/ScalesSmearings/Legacy2016_07Aug2017_FineEtaR9_v3_ele_unc"
    if era=="2016-Feb17ReMiniAOD":
        raise RuntimeError('Error in postRecoEgammaTools, era 2016-Feb17ReMiniAOD is not currently implimented')
    if era=="2018-Prompt":
        return "EgammaAnalysis/ElectronTools/data/ScalesSmearings/Run2018_Step2Closure_CoarseEtaR9Gain_v2"
    raise LogicError('Error in postRecoEgammaTools, era '+era+' not added to energy corrections function, please update this function')

def _is80XRelease(era):
    _check_valid_era(era)
    if era=="2016-Legacy" or era=="2016-Feb17ReMiniAOD": return True
    else: return False

def _is94XTo102XRelease(era):
    _check_valid_era(era)
    if era=="2017-Nov17ReReco" or era=="2018-Prompt": return True
    else: return False

def _getMVAsBeingRun(vidMod):
    mvasBeingRun = []
    for id_ in vidMod.physicsObjectIDs:
        for cut in id_.idDefinition.cutFlow:
            if cut.cutName.value().startswith("GsfEleMVA") or cut.cutName.value().startswith("PhoMVA"):
                mvaValueName = cut.mvaValueMapName.getProductInstanceLabel().replace("RawValues","Values")
                
                mvasBeingRun.append({'val' : {'prod' : cut.mvaValueMapName.getModuleLabel(),'name' : mvaValueName}, 'cat' : {'prod' : cut.mvaCategoriesMapName.getModuleLabel(),'name' : cut.mvaCategoriesMapName.getProductInstanceLabel() }})
    return mvasBeingRun
                
def _addMissingMVAValuesToUserData(process,egmod):

    if len(egmod)<2 or egmod[0].modifierName.value()!='EGExtraInfoModifierFromFloatValueMaps' or egmod[1].modifierName.value()!='EGExtraInfoModifierFromIntValueMaps':
        raise RuntimeError('dumping offending module {}\nError in postRecoEgammaTools._addMissingMVAValuesToUserData, we assume that the egamma_modifiers are setup so first its the float mod and then the int mod, this is currently not the case, the offending module dump is above'.format(egmod.dumpPython()))
    
    eleMVAs = _getMVAsBeingRun(process.egmGsfElectronIDs)
    phoMVAs = _getMVAsBeingRun(process.egmPhotonIDs)

    addVar = lambda modifier,var: setattr(modifier,var['name'],cms.InputTag(var['prod'],var['name']))
    
    for eleMVA in eleMVAs:
        if not hasattr(egmod[0].electron_config,eleMVA['val']['name']):
            addVar(egmod[0].electron_config,eleMVA['val'])
            addVar(egmod[1].electron_config,eleMVA['cat'])
    
    for phoMVA in phoMVAs:
        print phoMVA
        if not hasattr(egmod[0].photon_config,phoMVA['val']['name']):
            addVar(egmod[0].photon_config,phoMVA['val'])
            addVar(egmod[1].photon_config,phoMVA['cat'])


class CfgData:
    
    def __init__(self,args,kwargs):      
        self.defaults = {
            'applyEnergyCorrections' : False,
            'applyVIDOnCorrectedEgamma' : False,
            'isMiniAOD' : True,
            'era' : '2017-Nov17ReReco',
            'eleIDModules' : _defaultEleIDModules,
            'phoIDModules' : _defaultPhoIDModules,
            'runVID' : True,
            'runEnergyCorrections' : True,
            'applyEPCombBug' : False,
            'autoAdjustParams' : True,
            'process' : None
        }

        print args,kwargs
       
        if len(args)>1: 
            raise Exception('error multiple unnamed parameters pass to EgammaPostRecoTools')
        
        for k,v in self.defaults.iteritems():
            setattr(self,k,v)
        
        for k,v in kwargs.iteritems():
            if k not in self.defaults:
                raise Exception('error parameter {} not recognised'.format(k))
            setattr(self,k,v)
        
        if self.process == None:
            try:
                self.process = args[0]
            except IndexError:
                raise Exception('error, no "process" arguement passed')

##end utility functions

                                          
def _setupEgammaEnergyCorrectionsMiniAOD(eleSrc,phoSrc,cfg):
    """sets up the e/gamma energy corrections for miniAOD
    it will adjust eleSrc and phoSrc to the correct values

    it creates a task egammaScaleSmearTask with the modules to run
    """

    process = cfg.process

    process.egammaScaleSmearTask = cms.Task()  
    if cfg.runEnergyCorrections == False:
        return

    process.load('RecoEgamma.EgammaTools.calibratedEgammas_cff')
    #we copy the input tag as we may change them later
    process.calibratedPatElectrons.src = eleSrc
    process.calibratedPatPhotons.src = phoSrc
    
    energyCorrectionFile = _getEnergyCorrectionFile(cfg.era)
    process.calibratedPatElectrons.correctionFile = energyCorrectionFile
    process.calibratedPatPhotons.correctionFile = energyCorrectionFile

    if cfg.applyEPCombBug and hasattr(process.calibratedPatElectrons,'useSmearCorrEcalEnergyErrInComb'):
        process.calibratedPatElectrons.useSmearCorrEcalEnergyErrInComb=True
    elif hasattr(process.calibratedPatElectrons,'useSmearCorrEcalEnergyErrInComb'):
        process.calibratedPatElectrons.useSmearCorrEcalEnergyErrInComb=False
    elif cfg.applyEPCombBug:
        raise RuntimeError('Error in postRecoEgammaTools, the E/p combination bug can not be applied in >= 10_2_X (applyEPCombBug must be False) , it is only possible to emulate in 9_4_X')

    process.egammaScaleSmearTask.add(process.calibratedPatElectrons)
    process.egammaScaleSmearTask.add(process.calibratedPatPhotons)

    if cfg.applyEnergyCorrections or cfg.applyVIDOnCorrectedEgamma:
        process.calibratedPatElectrons.produceCalibratedObjs = True
        process.calibratedPatPhotons.produceCalibratedObjs = True
        return cms.InputTag("calibratedPatElectrons"),cms.InputTag("calibratedPatPhotons")
    else:
        process.calibratedPatElectrons.produceCalibratedObjs = False 
        process.calibratedPatPhotons.produceCalibratedObjs = False 
        return cms.InputTag(eleSrc.value()),cms.InputTag(phoSrc.value())
    
def _setupEgammaUpdatorMiniAOD(eleSrc,phoSrc,cfg):
    """
    This function updates the electrons and photons to form the basis for VID/energy correction
    Examples are updates to new dataformats and applications of the energy regression
    it only runs the updator if there is something to update
    
    defines a task egammaUpdatorTask which may or may not be empty
    
    """
    process = cfg.process
    process.egammaUpdatorTask = cms.Task()

    modifiers = cms.VPSet()
    from RecoEgamma.EgammaTools.egammaObjectModificationsInMiniAOD_cff import egamma8XObjectUpdateModifier,egamma9X105XUpdateModifier

    if _is80XRelease(cfg.era): modifiers.append(egamma8XObjectUpdateModifier)
    if _is94XTo102XRelease(cfg.era): 
        #we have to add the modules to produce the variables needed to update the to new dataformat to the task
        process.load('RecoEgamma.ElectronIdentification.heepIdVarValueMapProducer_cfi')
        process.load('RecoEgamma.PhotonIdentification.photonIDValueMapProducer_cff')
        process.load('RecoEgamma.EgammaIsolationAlgos.egmPhotonIsolationMiniAOD_cff')
        process.heepIDVarValueMaps.elesMiniAOD = eleSrc
        process.photonIDValueMapProducer.srcMiniAOD = phoSrc
        process.egmPhotonIsolation.srcToIsolate = phoSrc
        #now disabling miniAOD/AOD auto detection...
        process.heepIDVarValueMaps.dataFormat = 2 
        process.photonIDValueMapProducer.src = cms.InputTag("") 
        process.egammaUpdatorTask.add(process.heepIDVarValueMaps,process.egmPhotonIsolation,process.photonIDValueMapProducer)
        modifiers.append(egamma9X105XUpdateModifier)

    if modifiers != cms.VPSet():
        process.updatedElectrons = cms.EDProducer("ModifiedElectronProducer",
                                                  src=eleSrc,
                                                  modifierConfig = cms.PSet(
                                                      modifications = modifiers
                                                      )
                                                  )
        
        process.updatedPhotons = cms.EDProducer("ModifiedPhotonProducer",
                                                src=phoSrc,
                                                modifierConfig = cms.PSet(
                                                    modifications = modifiers
                                                    )
                                                )
        process.egammaUpdatorTask.add(process.updatedElectrons,process.updatedPhotons)
        return cms.InputTag("updatedElectrons"),cms.InputTag("updatedPhotons")
    else:
        return cms.InputTag(eleSrc.value()),cms.InputTag(phoSrc.value())

        
def _setupEgammaVIDMiniAOD(eleSrc,phoSrc,cfg):
    process = cfg.process
    process.egammaVIDTask = cms.Task()
    if cfg.runVID:
        process.egammaVIDTask.add(process.egmGsfElectronIDTask)
        process.egammaVIDTask.add(process.egmPhotonIDTask)
        process.egmGsfElectronIDs.physicsObjectSrc = eleSrc
        process.egmPhotonIDs.physicsObjectSrc = phoSrc
        process.electronMVAValueMapProducer.srcMiniAOD = eleSrc
        if hasattr(process,'electronMVAVariableHelper'):
            process.electronMVAVariableHelper.srcMiniAOD = eleSrc
        process.photonMVAValueMapProducer.srcMiniAOD = phoSrc 
        
        #process.photonIDValueMapProducer.srcMiniAOD = phoSrc
        #process.egmPhotonIsolation.srcToIsolate = phoSrc

        #we need to also zero out the AOD srcs as otherwise it gets confused in two tier jobs
        #and bad things happen
        process.electronMVAValueMapProducer.src = cms.InputTag("")
        process.photonMVAValueMapProducer.src = cms.InputTag("")
        process.photonIDValueMapProducer.src = cms.InputTag("")

    if cfg.runVID and hasattr(process,'heepIDVarValueMaps') and False:
        process.heepIDVarValueMaps.elesMiniAOD = eleSrc
        process.heepIDVarValueMaps.dataFormat = 2

    return eleSrc,phoSrc


def _setupEgammaEmbedderMiniAOD(eleSrc,phoSrc,cfg):
    from RecoEgamma.EgammaTools.egammaObjectModificationsInMiniAOD_cff import egamma_modifications,egamma8XLegacyEtScaleSysModifier
    from RecoEgamma.EgammaTools.egammaObjectModifications_tools import makeVIDBitsModifier,makeVIDinPATIDsModifier,makeEnergyScaleAndSmearingSysModifier  
    process = cfg.process
    if cfg.runVID:
        egamma_modifications.append(makeVIDBitsModifier(process,"egmGsfElectronIDs","egmPhotonIDs"))
        egamma_modifications.append(makeVIDinPATIDsModifier(process,"egmGsfElectronIDs","egmPhotonIDs"))
    else:
        egamma_modifications = cms.VPSet() #reset all the modifications which so far are just VID

    if cfg.runEnergyCorrections:
        egamma_modifications.append(makeEnergyScaleAndSmearingSysModifier("calibratedPatElectrons","calibratedPatPhotons"))
        egamma_modifications.append(egamma8XLegacyEtScaleSysModifier)
        
    
    #add any missing variables to the slimmed electron 
    if cfg.runVID:
        #MVA V2 values may not be added by default due to data format consistency issues
        _addMissingMVAValuesToUserData(process,egamma_modifications)
        #now add HEEP trk isolation
        #for pset in egamma_modifications:
        #    if pset.hasParameter("modifierName") and pset.modifierName == cms.string('EGExtraInfoModifierFromFloatValueMaps'):
         #       pset.electron_config.heepTrkPtIso = cms.InputTag("heepIDVarValueMaps","eleTrkPtIso")
          #      break

    for pset in egamma_modifications:
        pset.overrideExistingValues = cms.bool(True)
        if hasattr(pset,"electron_config"): pset.electron_config.electronSrc = eleSrc
        if hasattr(pset,"photon_config"): pset.photon_config.photonSrc = phoSrc

    process.slimmedElectrons = cms.EDProducer("ModifiedElectronProducer",
                                              src=eleSrc,
                                              modifierConfig = cms.PSet(
                                                  modifications = egamma_modifications
                                                  )
                                              )
    process.slimmedPhotons = cms.EDProducer("ModifiedPhotonProducer",
                                            src=phoSrc,
                                            modifierConfig = cms.PSet(
                                                modifications = egamma_modifications
                                                )
                                            )

    process.egammaPostRecoPatUpdatorTask = cms.Task()
    #we only run if the modifications are going to do something
    if egamma_modifications != cms.VPSet():
        process.egammaPostRecoPatUpdatorTask.add(process.slimmedElectrons)
        process.egammaPostRecoPatUpdatorTask.add(process.slimmedPhotons)
       
    return eleSrc,phoSrc

def _setupEgammaPostRECOSequenceMiniAOD(*args,**kwargs):
    """
    This function loads the calibrated producers calibratedPatElectrons,calibratedPatPhotons, 
    sets VID & other modules to the correct electron/photon source,
    loads up the modifiers and which then creates a new slimmedElectrons,slimmedPhotons collection
    with VID and scale and smearing all loaded in

    It runs internally in four steps

    1) update of the pre-vid object
    2) running VID
    3) update of the post-vid object

    """

    cfg = CfgData(args,kwargs)
    
    if cfg.applyEnergyCorrections != cfg.applyVIDOnCorrectedEgamma:
        raise RuntimeError('Error, applyEnergyCorrections {} and applyVIDOnCorrectedEgamma {} must be equal to each other for now,\n functionality for them to be different isnt yet availible'.format(applyEnergyCorrections,applyVIDOnCorrectedEgamma))


    phoSrc = cms.InputTag('slimmedPhotons',processName=cms.InputTag.skipCurrentProcess())
    eleSrc = cms.InputTag('slimmedElectrons',processName=cms.InputTag.skipCurrentProcess())

    eleSrc,phoSrc = _setupEgammaUpdatorMiniAOD(eleSrc=eleSrc,phoSrc=phoSrc,cfg=cfg)
    eleSrc,phoSrc = _setupEgammaEnergyCorrectionsMiniAOD(eleSrc=eleSrc,phoSrc=phoSrc,cfg=cfg)
    eleSrc,phoSrc = _setupEgammaVIDMiniAOD(eleSrc=eleSrc,phoSrc=phoSrc,cfg=cfg)
    eleSrc,phoSrc = _setupEgammaEmbedderMiniAOD(eleSrc=eleSrc,phoSrc=phoSrc,cfg=cfg)
    
    process = cfg.process
    
    process.egammaUpdatorSeq = cms.Sequence(process.egammaUpdatorTask)
    process.egammaScaleSmearSeq = cms.Sequence(process.egammaScaleSmearTask)
    process.egammaVIDSeq = cms.Sequence(process.egammaVIDTask)
    process.egammaPostRecoPatUpdatorSeq = cms.Sequence(process.egammaPostRecoPatUpdatorTask)

    process.egammaPostRecoSeq = cms.Sequence(
        process.egammaUpdatorSeq +
        process.egammaScaleSmearSeq +
        process.egammaVIDSeq + 
        process.egammaPostRecoPatUpdatorSeq
    )
        

def setupEgammaPostRecoSeq(process,
                           applyEnergyCorrections=False,
                           applyVIDOnCorrectedEgamma=False,
                           isMiniAOD=True,
                           era="2017-Nov17ReReco",
                           eleIDModules=_defaultEleIDModules,
                           phoIDModules=_defaultPhoIDModules,
                           runVID=True,
                           runEnergyCorrections=True,
                           applyEPCombBug=False,
                           autoAdjustParams=True):

    from PhysicsTools.SelectorUtils.tools.vid_id_tools import switchOnVIDElectronIdProducer,switchOnVIDPhotonIdProducer,setupAllVIDIdsInModule,DataFormat,setupVIDElectronSelection,setupVIDPhotonSelection
    # turn on VID producer, indicate data format  to be
    # DataFormat.AOD or DataFormat.MiniAOD, as appropriate
    if runVID:
        if isMiniAOD:
            switchOnVIDElectronIdProducer(process,DataFormat.MiniAOD)
            switchOnVIDPhotonIdProducer(process,DataFormat.MiniAOD)
        else:
            switchOnVIDElectronIdProducer(process,DataFormat.AOD)
            switchOnVIDPhotonIdProducer(process,DataFormat.AOD)

        for idmod in eleIDModules:
            setupAllVIDIdsInModule(process,idmod,setupVIDElectronSelection)
        for idmod in phoIDModules:
            setupAllVIDIdsInModule(process,idmod,setupVIDPhotonSelection)

    if autoAdjustParams:
        pass #no auto adjustment needed

    if isMiniAOD:
        _setupEgammaPostRECOSequenceMiniAOD(process,applyEnergyCorrections=applyEnergyCorrections,applyVIDOnCorrectedEgamma=applyVIDOnCorrectedEgamma,era=era,runVID=runVID,runEnergyCorrections=runEnergyCorrections,applyEPCombBug=applyEPCombBug)
    else:
      #  _setupEgammaPostRECOSequence(process,applyEnergyCorrections=applyEnergyCorrections,applyVIDOnCorrectedEgamma=applyVIDOnCorrectedEgamma,era=era,runVID=runVID,runEnergyCorrections=runEnergyCorrections,applyEPCombBug=applyEPCombBug)
        pass
  #  process.egammaScaleSmearSeq = cms.Sequence(process.egammaScaleSmearTask)
    #post reco seq is calibrations -> vid -> pat updator 
   # process.egammaPostRecoSeq   = cms.Sequence(process.egammaScaleSmearSeq)
   # if not runEnergyCorrections and runVID:
    #    process.egammaPostRecoSeq = cms.Sequence(process.egmGsfElectronIDSequence*process.egmPhotonIDSequence)
    #elif runVID:
    #    process.egammaPostRecoSeq.insert(-1,process.egmGsfElectronIDSequence)
    #    process.egammaPostRecoSeq.insert(-1,process.egmPhotonIDSequence)
    #if isMiniAOD:
     #   process.egammaPostRecoPatUpdatorSeq = cms.Sequence(process.egammaPostRecoPatUpdatorTask)
     #   process.egammaPostRecoSeq.insert(-1,process.egammaPostRecoPatUpdatorSeq)     
                       
    #return process


def makeEgammaPATWithUserData(process,eleTag=None,phoTag=None,runVID=True,runEnergyCorrections=True,era="2017-Nov17ReReco",suffex="WithUserData"):
    """
    This function embeds the value maps into a pat::Electron,pat::Photon
    This function is not officially supported by e/gamma and is on a best effort bais
    eleTag and phoTag are type cms.InputTag
    outputs new collection with {eleTag/phoTag}.moduleLabel + suffex 
    """
    from RecoEgamma.EgammaTools.egammaObjectModificationsInMiniAOD_cff import egamma_modifications,egamma8XLegacyEtScaleSysModifier,egamma8XObjectUpdateModifier
    from RecoEgamma.EgammaTools.egammaObjectModifications_tools import makeVIDBitsModifier,makeVIDinPATIDsModifier,makeEnergyScaleAndSmearingSysModifier  
    if runVID:
        egamma_modifications.append(makeVIDBitsModifier(process,"egmGsfElectronIDs","egmPhotonIDs"))
        egamma_modifications.append(makeVIDinPATIDsModifier(process,"egmGsfElectronIDs","egmPhotonIDs"))
    else:
        egamma_modifications = cms.VPSet() #reset all the modifications which so far are just VID
    if _is80XRelease(era): 
        egamma_modifications.append(egamma8XObjectUpdateModifier) #if we were generated in 80X, we need fill in missing data members in 94X
    if runEnergyCorrections:
        egamma_modifications.append(makeEnergyScaleAndSmearingSysModifier("calibratedElectrons","calibratedPhotons"))
        egamma_modifications.append(egamma8XLegacyEtScaleSysModifier)
    
    process.egammaPostRecoPatUpdatorTask = cms.Task()

    if eleTag:
        modName = eleTag.moduleLabel+suffex
        setattr(process,modName,cms.EDProducer("ModifiedElectronProducer",
                                               src=eleTag,
                                               modifierConfig = cms.PSet(
                                                 modifications = egamma_modifications
                                                 )      
                                               ))
        process.egammaPostRecoPatUpdatorTask.add(getattr(process,modName))

    if phoTag:
        modName = phoTag.moduleLabel+suffex
        setattr(process,modName,cms.EDProducer("ModifiedPhotonProducer",
                                               src=phoTag,
                                               modifierConfig = cms.PSet(
                                                 modifications = egamma_modifications
                                                 )
                                               )) 
        process.egammaPostRecoPatUpdatorTask.add(getattr(process,modName))
        
    process.egammaPostRecoPatUpdatorSeq = cms.Sequence(process.egammaPostRecoPatUpdatorTask)
    return process