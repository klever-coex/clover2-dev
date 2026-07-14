variable "BUILD_MODE" { }
variable "DOCKER_OUTPUT_DIR" { }
variable "REGISTRY_POLICY" { }
variable "REGISTRY" { default = "ghcr.io/klever-coex/clover2-dev/" }
variable "ROS_DISTRO" { default = "jazzy" }

variable "CLOVER2_DEV_GIT_HASH" { }

variable "USE_REGISTRY_CONTEXTS" {
  default = true
}

variable "LABELS" {
  default = {
    "org.opencontainers.image.authors"  = "Lapin Matvey"
    "org.opencontainers.image.licenses" = "MIT"
    "org.opencontainers.image.source"   = "https://github.com/klever-coex/clover2-dev"
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
    result = compact(concat(
        ["${REGISTRY}${name}:${CLOVER2_DEV_GIT_HASH}"],

        # For master build have dirty version and latest tag
        BUILD_MODE == "master" ? ["${REGISTRY}${name}:latest"] : [],

        # For develop build have dirty version tag
        # Only version tag
    ))
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

  cache-from = ["type=local,src=.cache/docker"]
  cache-to   = ["type=local,dest=.cache/docker,mode=max"]
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
