variable "BUILD_MODE" { }
variable "REGISTRY" { default = "ghcr.io/klever-coex/clover2-dev/" }
variable "ROS_DISTRO" { default = "jazzy" }

variable "CLOVER2_DEV_GIT_HASH" { }
variable "CLOVER2_DEV_VERSION" { }

variable "USE_REGISTRY_CONTEXTS" {
  default = true
}

variable "LOCAL_CACHE" {
  default = ""
}

variable "LABELS" {
  default = {
    "org.opencontainers.image.authors"  = "Lapin Matvey"
    "org.opencontainers.image.licenses" = "MIT"
    "org.opencontainers.image.source"   = "https://github.com/klever-coex/clover2-dev"
    "org.opencontainers.image.version"  = CLOVER2_DEV_VERSION
    "org.opencontainers.image.revision" = CLOVER2_DEV_GIT_HASH
  }
}

# Platforms for deploy
variable "PLATFORMS" {
  default = [
    "linux/amd64",
  ]
}

# Image tags generator
function "tagged" {
  params = [name]
  result = compact([
    "${REGISTRY}${name}:${CLOVER2_DEV_GIT_HASH}",

    # For master build have dirty version and latest tag
    equal("master", BUILD_MODE) ? "${REGISTRY}${name}:latest" : null,

    # For develop build have dirty version tag
    # Only version tag

    # Releases have version and stable tags
    equal("release", BUILD_MODE) ? "${REGISTRY}${name}:stable" : null,
    equal("release", BUILD_MODE) ? "${REGISTRY}${name}:${CLOVER2_DEV_VERSION}" : null,

    # Pre-releases (e.g. 0.2.0-rc.1) have version and pre-release tags
    equal("pre-release", BUILD_MODE) ? "${REGISTRY}${name}:pre-release" : null,
    equal("pre-release", BUILD_MODE) ? "${REGISTRY}${name}:${CLOVER2_DEV_VERSION}" : null,
  ])
}

function "ctx" {
  params = [image_name, target_name]
  result = USE_REGISTRY_CONTEXTS ? "docker-image://${tagged(image_name)[0]}" : "target:${target_name}"
}

target "_base" {
  context = "."
  labels = LABELS

  args = {
    CLOVER2_DEV_GIT_HASH = "${CLOVER2_DEV_GIT_HASH}"
  }

  cache-from = LOCAL_CACHE == "1" ? ["type=local,src=.cache/docker"] : []
  cache-to   = LOCAL_CACHE == "1" ? ["type=local,dest=.cache/docker,mode=max"] : []
}

group "default" {
  targets = ["base", "core-devel"]
}

target "base" {
  dockerfile = "docker/base.Dockerfile"
  target     = "base"
  tags       = tagged("clover2-base")

  inherits = ["_base"]

  args = {
    ROS_DISTRO = ROS_DISTRO
  }
}

target "core-devel" {
  dockerfile = "docker/core.Dockerfile"
  target     = "core-devel"
  tags       = tagged("clover2-core")

  inherits = ["_base"]

  contexts = {
    clover2-base = ctx("clover2-base", "base")
  }

  args = {
    BASE_IMAGE = "clover2-base"
    ROS_DISTRO = ROS_DISTRO
  }
}
