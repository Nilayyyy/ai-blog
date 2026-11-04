---
title: "Getting Started with OCI: The Five Services Worth Learning First"
description: "A practical guide for developers to navigate Oracle Cloud Infrastructure by focusing on the five core services that provide the most utility."
pubDate: 2026-11-04
tags: [oci, cloud, infrastructure, development, cloud-computing]
canonical:
---

If you are moving from AWS, GCP, or Azure to Oracle Cloud Infrastructure (OCI), the platform might look familiar, but the underlying architecture has distinct organizational requirements. OCI is built with a focus on resource isolation and explicit networking control. Before you deploy your first workload, you need to understand how the platform organizes resources and secures them.

## The OCI Mental Model: Understanding Compartments and Tenancy

In OCI, your account is called a **Tenancy**. Everything you create lives inside this tenancy. The primary unit of organization is the **Compartment**.

Think of a compartment as a logical container. Unlike other clouds that use tags or resource groups for organization, OCI uses compartments to apply security policies and billing. You cannot move a resource to another compartment once it is created; you must recreate it if you need to reorganize. 

When you start, you have a "Root" compartment. Do not deploy production resources directly into Root. Create a hierarchy, such as `Production`, `Staging`, and `Development` compartments. This structure allows you to write one IAM policy that grants a developer access to everything in `Development` without giving them permissions for `Production`.

## Compute Instances: Provisioning VMs and Bare Metal

Provisioning a compute instance in OCI is straightforward, but the choice between Virtual Machines (VMs) and Bare Metal instances is significant. VMs behave like instances in other clouds: you share underlying hardware, and you can resize them.

Bare Metal instances give you direct access to the physical server. There is no hypervisor layer between your code and the hardware. This is useful for high-performance computing, large databases, or applications that need to manage their own virtualization.

When you provision an instance, you select an **Availability Domain (AD)** or a **Fault Domain (FD)**. ADs are separate physical data centers within a region. FDs are logical groupings within an AD that protect against hardware failure or maintenance. Always distribute your instances across different FDs to ensure high availability.

## Block and Object Storage: Managing Data Persistence

Data persistence in OCI is divided into two categories: Block Volumes and Object Storage.

**Block Storage** acts like a hard drive attached to your compute instance. It is high-performance and low-latency. You use it for operating systems, application files, and databases. If you stop your instance, the data remains on the block volume. You can detach a volume from one instance and attach it to another within the same AD.

**Object Storage** is for unstructured data: logs, backups, images, or large datasets. It is not attached to a server. You access it via an API or a URL. It is highly durable and scales automatically. Object storage is organized into "buckets." Use it for static assets or data that needs to be accessed by multiple services simultaneously.

## Virtual Cloud Networks (VCN): Designing Your Network Perimeter

A VCN is your private network space. You define the IP address range using a CIDR block. 

Inside the VCN, you define **Subnets**. OCI subnets are tied to a single availability domain. You choose between public subnets (accessible from the internet) and private subnets (hidden behind a NAT gateway).

Security is managed through **Security Lists** and **Network Security Groups (NSGs)**:
*   **Security Lists:** These act as a firewall at the subnet level. Any instance in that subnet is subject to these rules.
*   **Network Security Groups:** These act at the VNIC (Virtual Network Interface Card) level. They are more granular and allow you to define rules based on the specific instance, regardless of the subnet.

Always default to private subnets for your compute instances and use a Load Balancer or Bastion service to control traffic flow.

## Identity and Access Management (IAM): Controlling Resource Permissions

IAM in OCI is policy-driven. A policy is a statement that says, "Group X can do Y to resource Z in compartment A." 

The syntax follows this pattern:
`Allow group [GroupName] to [Verb] [ResourceType] in compartment [CompartmentName]`

*   **Verbs:** `inspect`, `read`, `use`, `manage`.
*   **ResourceTypes:** `instances`, `buckets`, `volumes`, etc.

Do not use the Administrator account for daily tasks. Create groups based on roles, such as `AppDevelopers` or `NetworkAdmins`, and assign users to those groups. Use the "Principle of Least Privilege" by granting only the permissions necessary for the task. 

## Automation: CLI and Terraform

Once you are comfortable with the web console, move to automation. OCI provides a robust CLI and an official Terraform provider.

The OCI CLI is a wrapper around the REST API. You can install it on your local machine and configure it using the `oci setup config` command.

For infrastructure, use Terraform. OCI maintains an official Terraform provider that allows you to manage your VCNs, compute instances, and storage as code. 

Example snippet for provisioning a basic VCN:

```hcl
resource "oci_core_vcn" "main_vcn" {
  cidr_block     = "10.0.0.0/16"
  compartment_id = var.compartment_ocid
  display_name   = "main-vcn"
}
```

Start by creating a simple VCN and a single VM using Terraform. Once you see the resources appear in your console, you will understand how OCI translates API calls into physical infrastructure. Focus on mastering the VCN and IAM components first; the rest of the ecosystem builds on these two foundations.

