# Detailed vehicles and aircraft

The six new car choices now use detailed licensed model assets instead of the previous procedural blockouts. The official DrivAer sedan is unchanged.

| Choice | Source and author | License | Zephyr changes |
| --- | --- | --- | --- |
| Impreza hatchback | Stunt Rally S8, lubomircenovsky; [original](https://www.blendswap.com/blends/view/47523) | CC BY-SA 3.0 | Coordinate conversion, material conversion, wheel placement |
| Touring wagon | Same S8 asset | CC BY-SA 3.0 | Extended passenger/cargo section by 0.65 m, unchanged front and round wheels, recolored paint; a generic derivative, not a production Impreza wagon |
| Hummer SUV | Stunt Rally HR, thiagohenrinrique; CryHam import/interior/settings; [original](https://www.blendswap.com/blends/view/66599) | CC BY, as specified in upstream notice | Coordinate/material conversion, wheel placement |
| M3 coupe | Stunt Rally XZ, Neubi; CryHam import/interior/settings; [original](https://www.blendswap.com/blends/view/19869) | CC0, as specified in upstream notice | Coordinate/material conversion, wheel placement |
| Veneno sports car | Stunt Rally Y7, hasapeta; CryHam import/settings; [original](https://www.blendswap.com/blends/view/74455) | CC BY, as specified in upstream notice | Coordinate/material conversion, wheel placement, gold paint |
| Sprinter van | [Cyberbotics Webots MercedesBenzSprinterSimple](https://github.com/cyberbotics/webots/tree/master/projects/vehicles/protos/mercedes_benz) | Apache 2.0 (source PROTO license) | OBJ parts assembled, uniform size reduction, materials converted; HR wheels reused under their upstream CC BY notice |
| NASA X-57 | [NASA 3D Resources](https://github.com/nasa/NASA-3D-Resources/tree/master/3D%20Models/X-57) | NASA public educational/informational use | Draco decoding, visual mesh reduction, material adjustment, uniform scale to 3.3 m wingspan |
| NASA Global Hawk | [NASA 3D Resources](https://github.com/nasa/NASA-3D-Resources/tree/master/3D%20Models/Global%20Hawk) | NASA public educational/informational use | Draco decoding, orientation conversion, uniform scale to 3.3 m wingspan |

Stunt Rally source meshes: https://github.com/stuntrally/stuntrally/tree/master/data/cars
Current textures and author notices: https://github.com/stuntrally/stuntrally3/tree/main/data/cars

The S8-derived GLBs and derived geometry previews are distributed under [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/). Other converted models retain their upstream licenses. Exact source-file notices, SHA-256 hashes, and pinned download URLs are recorded in the repository's `config/vehicle-source-artifacts.json`. No manufacturer, NASA, Cyberbotics, or model author endorses Zephyr. Vehicle names identify the depicted assets. NASA marks remain part of the depicted aircraft, not Zephyr branding.

NASA usage guidelines: https://www.nasa.gov/nasa-brand-center/images-and-media/
Apache 2.0: https://www.apache.org/licenses/LICENSE-2.0
CC0: https://creativecommons.org/publicdomain/zero/1.0/

The detailed visual meshes are not CFD meshes. Zephyr derives a closed, simplified surface from each model for experimental NVIDIA inference. The aircraft are scaled display experiments, not validated aircraft simulations. The original DrivAer and concept-coupe credits remain in `ATTRIBUTION.md`.
