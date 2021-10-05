# Databricks notebook source
# addcol.py
# Making some changes from Feature branch2
import pyspark.sql.functions as F

def with_status(df):
    return df.withColumn("status", F.lit("checked"))
